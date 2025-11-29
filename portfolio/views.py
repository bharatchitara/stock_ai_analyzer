from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.db.models import Q, Sum, Avg
from decimal import Decimal
from datetime import datetime, date, timedelta
import json

from news.models import (
    Stock, NewsArticle, UserPortfolio, PortfolioHolding, 
    PersonalizedRecommendation
)
from analysis.ai_analyzer import RecommendationEngine
from .importers import PortfolioImporter
from .stock_fetcher import StockPriceFetcher
from .task_progress import TaskProgress
import uuid


def get_default_user():
    """Get or create a default user for the application"""
    User = get_user_model()
    user = User.objects.first()
    if not user:
        user = User.objects.create_user(username='default_user', password='temp123')
    return user


def portfolio_dashboard(request):
    """Main portfolio dashboard view"""
    # Get or create portfolio for first user
    from django.contrib.auth import get_user_model
    User = get_user_model()
    first_user = User.objects.first()
    
    if not first_user:
        # Create a default user if none exists
        first_user = User.objects.create_user(username='default_user', password='temp123')
    
    user_portfolio, created = UserPortfolio.objects.get_or_create(user=first_user)
    
    # Get all holdings
    holdings = user_portfolio.holdings.select_related('stock').all()
    
    # Get personalized recommendations
    recommendations = PersonalizedRecommendation.objects.filter(
        holding__portfolio=user_portfolio,
        is_active=True
    ).select_related('holding__stock').order_by('-created_at', '-priority')[:10]
    
    # Build portfolio summary for template
    portfolio = {
        'total_investment': user_portfolio.total_investment_value,
        'current_value': user_portfolio.total_current_value,
        'total_pnl': user_portfolio.total_pnl,
        'total_pnl_percent': user_portfolio.total_pnl_percentage,
    }
    
    # Add computed properties to holdings for template
    for holding in holdings:
        holding.total_investment = holding.total_value
        holding.profit_loss = holding.pnl
        holding.return_percent = holding.pnl_percentage
        holding.current_price = holding.stock.current_price or holding.average_price
    
    context = {
        'portfolio': portfolio,
        'holdings': holdings,
        'recommendations': recommendations,
    }
    
    return render(request, 'portfolio/dashboard.html', context)


def add_holding(request):
    """Add a new stock holding to portfolio"""
    if request.method == 'POST':
        try:
            # Get or create portfolio
            portfolio, created = UserPortfolio.objects.get_or_create(user=get_default_user())
            
            # Extract form data
            stock_symbol = request.POST.get('stock_symbol').upper()
            quantity = int(request.POST.get('quantity'))
            average_price = Decimal(request.POST.get('average_price'))
            purchase_date = datetime.strptime(request.POST.get('purchase_date'), '%Y-%m-%d').date()
            notes = request.POST.get('notes', '')
            
            # Get or create stock
            stock, stock_created = Stock.objects.get_or_create(
                symbol=stock_symbol,
                defaults={
                    'company_name': stock_symbol,
                    'sector': 'Unknown'
                }
            )
            if stock_created:
                messages.info(request, f'New stock {stock_symbol} added to database.')
            
            # Check if holding already exists
            existing_holding = PortfolioHolding.objects.filter(
                portfolio=portfolio,
                stock=stock
            ).first()
            
            if existing_holding:
                # Update existing holding (average price calculation)
                total_shares = existing_holding.quantity + quantity
                total_investment = (existing_holding.quantity * existing_holding.average_price) + (quantity * average_price)
                new_average_price = total_investment / total_shares
                
                existing_holding.quantity = total_shares
                existing_holding.average_price = new_average_price
                existing_holding.notes = f"{existing_holding.notes}\n{notes}".strip()
                existing_holding.save()
                
                messages.success(request, f'Updated holding for {stock.symbol}. New average price: ₹{new_average_price:.2f}')
            else:
                # Create new holding
                PortfolioHolding.objects.create(
                    portfolio=portfolio,
                    stock=stock,
                    quantity=quantity,
                    average_price=average_price,
                    purchase_date=purchase_date,
                    notes=notes
                )
                messages.success(request, f'Added {quantity} shares of {stock.symbol} to your portfolio')
            
            # Fetch current price for the stock
            fetcher = StockPriceFetcher()
            price_result = fetcher.fetch_price(stock.symbol)
            
            if price_result['success']:
                stock.current_price = price_result['current_price']
                stock.price_updated_at = price_result['timestamp']
                stock.save(update_fields=['current_price', 'price_updated_at'])
                messages.info(request, f'Current price updated: ₹{price_result["current_price"]}')
            
            # Generate personalized recommendations for this stock
            generate_holding_recommendations(portfolio, stock)
            
        except Exception as e:
            messages.error(request, f'Error adding holding: {str(e)}')
    
    return redirect('portfolio:dashboard')


def remove_holding(request, holding_id):
    """Remove a holding from portfolio"""
    portfolio = get_object_or_404(UserPortfolio, user=get_default_user())
    holding = get_object_or_404(PortfolioHolding, id=holding_id, portfolio=portfolio)
    
    stock_symbol = holding.stock.symbol
    holding.delete()
    
    messages.success(request, f'Removed {stock_symbol} from your portfolio')
    return redirect('portfolio:dashboard')


def update_holding(request, holding_id):
    """Update a portfolio holding"""
    if request.method == 'POST':
        portfolio = get_object_or_404(UserPortfolio, user=get_default_user())
        holding = get_object_or_404(PortfolioHolding, id=holding_id, portfolio=portfolio)
        
        try:
            holding.quantity = int(request.POST.get('quantity'))
            holding.average_price = Decimal(request.POST.get('average_price'))
            holding.purchase_date = datetime.strptime(request.POST.get('purchase_date'), '%Y-%m-%d').date()
            holding.notes = request.POST.get('notes', '')
            holding.save()
            
            messages.success(request, f'Updated holding for {holding.stock.symbol}')
            
            # Regenerate recommendations
            generate_holding_recommendations(holding.portfolio, holding.stock)
            
        except Exception as e:
            messages.error(request, f'Error updating holding: {str(e)}')
    
    return redirect('portfolio:dashboard')


def portfolio_analytics(request):
    """Portfolio analytics and insights"""
    portfolio = get_object_or_404(UserPortfolio, user=get_default_user())
    holdings = portfolio.holdings.select_related('stock').all()
    
    # Sector allocation with detailed metrics
    sector_allocation = {}
    for holding in holdings:
        sector = holding.stock.sector or 'Unknown'
        if sector not in sector_allocation:
            sector_allocation[sector] = {
                'investment': 0,
                'current_value': 0,
                'pnl': 0,
                'pnl_percent': 0,
                'allocation_percent': 0
            }
        sector_allocation[sector]['investment'] += holding.total_value
        sector_allocation[sector]['current_value'] += holding.current_value
    
    # Calculate sector P&L and allocation percentages
    total_investment = portfolio.total_investment_value or 1
    for sector, data in sector_allocation.items():
        data['pnl'] = data['current_value'] - data['investment']
        data['pnl_percent'] = (data['pnl'] / data['investment'] * 100) if data['investment'] > 0 else 0
        data['allocation_percent'] = (data['investment'] / total_investment * 100) if total_investment > 0 else 0
    
    # Top gainers and losers
    profitable_holdings = [h for h in holdings if h.is_profitable]
    loss_holdings = [h for h in holdings if not h.is_profitable]
    
    profitable_holdings.sort(key=lambda x: x.pnl_percentage, reverse=True)
    loss_holdings.sort(key=lambda x: x.pnl_percentage)
    
    # Best and worst performers
    best_performer = profitable_holdings[0] if profitable_holdings else None
    worst_performer = loss_holdings[0] if loss_holdings else None
    
    # Add computed properties to all holdings for template
    for holding in holdings:
        holding.return_percent = holding.pnl_percentage
        holding.profit_loss = holding.pnl
    
    # Prepare chart data
    sector_chart_data = {
        'labels': list(sector_allocation.keys()),
        'values': [data['investment'] for data in sector_allocation.values()]
    }
    
    pnl_chart_data = {
        'labels': [h.stock.symbol for h in holdings[:10]],
        'values': [h.pnl for h in holdings[:10]],
        'colors': ['rgba(40, 167, 69, 0.8)' if h.pnl >= 0 else 'rgba(220, 53, 69, 0.8)' for h in holdings[:10]]
    }
    
    # Analytics summary
    analytics = {
        'total_stocks': holdings.count(),
        'gainers_count': len(profitable_holdings),
        'losers_count': len(loss_holdings),
        'best_performer': best_performer,
        'worst_performer': worst_performer,
        'sector_allocation': sector_allocation,
        'sector_chart_data': json.dumps(sector_chart_data),
        'pnl_chart_data': json.dumps(pnl_chart_data),
        'top_gainers': profitable_holdings[:5],
        'top_losers': loss_holdings[:5],
    }
    
    context = {
        'portfolio': portfolio,
        'holdings': holdings,
        'analytics': analytics,
    }
    
    return render(request, 'portfolio/analytics.html', context)


def search_stocks(request):
    """AJAX endpoint to search stocks for adding to portfolio"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'stocks': []})
    
    stocks = Stock.objects.filter(
        Q(symbol__icontains=query) | Q(company_name__icontains=query)
    ).values('symbol', 'company_name', 'sector')[:10]
    
    return JsonResponse({'stocks': list(stocks)})


def generate_holding_recommendations(portfolio, stock):
    """Generate personalized recommendations for a specific holding"""
    try:
        holding = PortfolioHolding.objects.get(portfolio=portfolio, stock=stock)
        
        # Get recent news articles about this stock
        recent_articles = NewsArticle.objects.filter(
            mentioned_stocks=stock,
            published_at__gte=datetime.now() - timedelta(days=7)
        ).order_by('-published_at')
        
        if not recent_articles.exists():
            return
        
        # Analyze sentiment for this specific stock
        engine = RecommendationEngine()
        
        # Convert articles to the format expected by the recommendation engine
        article_data = []
        for article in recent_articles:
            article_data.append({
                'id': article.id,
                'sentiment': article.sentiment,
                'sentiment_score': article.sentiment_score or 0.5,
                'impact_level': article.impact_level,
                'category': article.category.name if article.category else 'OTHER',
                'mentioned_stocks': [stock.symbol]
            })
        
        # Generate recommendation
        recommendations = engine.generate_stock_recommendations(article_data)
        stock_rec = next((r for r in recommendations if r['stock_symbol'] == stock.symbol), None)
        
        if not stock_rec:
            return
        
        # Map general recommendation to portfolio-specific recommendation
        rec_mapping = {
            'BUY': 'BUY_MORE',
            'SELL': 'SELL_PARTIAL',
            'HOLD': 'HOLD',
            'WATCH': 'WATCH'
        }
        
        portfolio_rec = rec_mapping.get(stock_rec['recommendation'], 'HOLD')
        
        # Determine priority based on confidence and current P&L
        if stock_rec['confidence_level'] > 80:
            priority = 'HIGH'
        elif stock_rec['confidence_level'] > 60:
            priority = 'MEDIUM'
        else:
            priority = 'LOW'
        
        # Adjust recommendation based on current holding performance
        if holding.pnl_percentage < -10 and portfolio_rec == 'SELL_PARTIAL':
            priority = 'HIGH'  # High priority to limit losses
        elif holding.pnl_percentage > 20 and portfolio_rec == 'HOLD':
            portfolio_rec = 'SELL_PARTIAL'  # Consider booking profits
            priority = 'MEDIUM'
        
        # Deactivate old recommendations
        PersonalizedRecommendation.objects.filter(
            holding=holding,
            is_active=True
        ).update(is_active=False)
        
        # Create new recommendation
        PersonalizedRecommendation.objects.create(
            holding=holding,
            recommendation=portfolio_rec,
            priority=priority,
            confidence_score=stock_rec['confidence_level'] / 100,
            reasoning=stock_rec['reasoning'],
            key_factors=stock_rec.get('key_factors', []),
            target_price=None,  # Could be enhanced with price prediction
            stop_loss_price=None,  # Could be calculated based on risk tolerance
        )
        
    except Exception as e:
        print(f"Error generating recommendation for {stock.symbol}: {str(e)}")
        pass


def import_portfolio(request):
    """Import portfolio from file, image, or broker"""
    if request.method == 'POST':
        print("DEBUG: POST request received")
        print(f"DEBUG: POST data: {request.POST}")
        print(f"DEBUG: FILES: {request.FILES}")
        
        try:
            # Get import method
            import_method = request.POST.get('import_method', 'file')
            print(f"DEBUG: import_method = {import_method}")
            
            if import_method == 'file':
                return handle_file_import(request)
            elif import_method == 'image':
                return handle_image_import(request)
            elif import_method == 'broker':
                return handle_broker_import(request)
            else:
                messages.error(request, 'Invalid import method')
                return redirect('portfolio:import_portfolio')
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f'Import error: {str(e)}')
            return redirect('portfolio:import_portfolio')
    
    # GET request - show import form
    try:
        supported_brokers = list(PortfolioImporter.BROKER_FORMATS.keys())
    except:
        supported_brokers = []
    
    return render(request, 'portfolio/import.html', {
        'supported_brokers': supported_brokers
    })


def  handle_file_import(request):
    """Handle file upload (CSV/JSON) import"""
    uploaded_file = request.FILES.get('portfolio_file')
    broker = request.POST.get('broker', 'generic')
    
    print(f"DEBUG: handle_file_import called")
    print(f"DEBUG: uploaded_file = {uploaded_file}")
    print(f"DEBUG: broker = {broker}")
    print(f"DEBUG: FILES keys = {list(request.FILES.keys())}")
    
    if not uploaded_file:
        messages.error(request, 'No file uploaded. Please select a CSV or JSON file.')
        return redirect('portfolio:import_portfolio')
    
    # Show progress message
    messages.info(request, '📁 Importing portfolio... This may take a few moments.')
    
    try:
        # Read file content
        try:
            file_content = uploaded_file.read().decode('utf-8')
            print(f"DEBUG: File read successfully, length = {len(file_content)}")
        except Exception as e:
            print(f"DEBUG: Error reading file: {str(e)}")
            messages.error(request, f'Error reading file: {str(e)}')
            return redirect('portfolio:import_portfolio')
        
        # Initialize importer
        importer = PortfolioImporter()
        print(f"DEBUG: Importer initialized")
        
        # Parse based on file type
        if uploaded_file.name.endswith('.csv'):
            print(f"DEBUG: Parsing CSV file")
            holdings = importer.parse_csv(file_content, broker)
            print(f"DEBUG: Parsed {len(holdings)} holdings from CSV")
        elif uploaded_file.name.endswith('.json'):
            print(f"DEBUG: Parsing JSON file")
            holdings = importer.parse_json(file_content)
            print(f"DEBUG: Parsed {len(holdings)} holdings from JSON")
        else:
            messages.error(request, 'Unsupported file format. Use CSV or JSON.')
            return redirect('portfolio:import_portfolio')
        
        # Import holdings to database
        print(f"DEBUG: Getting or creating portfolio for default user")
        portfolio, created = UserPortfolio.objects.get_or_create(user=get_default_user())
        print(f"DEBUG: Portfolio created={created}, id={portfolio.id}")
        
        # Check if user wants to replace existing holdings
        replace_existing = request.POST.get('replace_existing') == 'on'
        print(f"DEBUG: replace_existing = {replace_existing}")
        
        if replace_existing:
            # Delete all existing holdings
            deleted_count = portfolio.holdings.count()
            portfolio.holdings.all().delete()
            print(f"DEBUG: Deleted {deleted_count} existing holdings")
            messages.info(request, f'Cleared {deleted_count} existing holdings before import')
        
        imported_count = 0
        skipped_count = 0
        updated_count = 0
        
        print(f"DEBUG: Processing {len(holdings)} holdings")
        for i, holding_data in enumerate(holdings):
            print(f"DEBUG: Processing holding {i+1}: {holding_data}")
            try:
                # Find or create stock
                stock = Stock.objects.filter(symbol=holding_data['symbol']).first()
                print(f"DEBUG: Stock lookup for {holding_data['symbol']}: {'found' if stock else 'not found'}")
                
                if not stock:
                    # Create the stock if it doesn't exist
                    print(f"DEBUG: Creating stock {holding_data['symbol']}")
                    stock = Stock.objects.create(
                        symbol=holding_data['symbol'],
                        company_name=holding_data['symbol'],  # Use symbol as company name temporarily
                        sector='Unknown'
                    )
                    print(f"DEBUG: Stock created: {stock.symbol}")
                
                # Continue with import even if stock was just created
                
                if not replace_existing:
                    # Check if holding already exists (only if not replacing)
                    existing_holding = PortfolioHolding.objects.filter(
                        portfolio=portfolio,
                        stock=stock
                    ).first()
                    print(f"DEBUG: Existing holding: {'found' if existing_holding else 'not found'}")
                    
                    if existing_holding:
                        # Update existing holding by adding quantities
                        print(f"DEBUG: Updating existing holding")
                        total_shares = existing_holding.quantity + holding_data['quantity']
                        total_investment = (
                            existing_holding.quantity * existing_holding.average_price +
                            holding_data['quantity'] * holding_data['avg_price']
                        )
                        new_average_price = total_investment / total_shares
                        
                        existing_holding.quantity = total_shares
                        existing_holding.average_price = new_average_price
                        existing_holding.notes = f"{existing_holding.notes}\nImported: {holding_data['quantity']} @ ₹{holding_data['avg_price']}".strip()
                        existing_holding.save()
                        
                        updated_count += 1
                        print(f"DEBUG: Updated holding for {stock.symbol}")
                        continue
                
                # Create new holding (either replace mode or no existing holding)
                print(f"DEBUG: Creating new holding")
                PortfolioHolding.objects.create(
                    portfolio=portfolio,
                    stock=stock,
                    quantity=holding_data['quantity'],
                    average_price=holding_data['avg_price'],
                    purchase_date=holding_data['purchase_date'],
                    notes=f"Imported from {broker}"
                )
                imported_count += 1
                print(f"DEBUG: Created new holding for {stock.symbol}")
                
                # Generate recommendations for this stock (skip if function doesn't exist)
                try:
                    generate_holding_recommendations(portfolio, stock)
                except:
                    pass
                
            except Exception as e:
                print(f"DEBUG: Error importing {holding_data.get('symbol', 'unknown')}: {str(e)}")
                import traceback
                traceback.print_exc()
                importer.errors.append(f"Error importing {holding_data.get('symbol', 'unknown')}: {str(e)}")
                continue
        
        # Get import summary
        summary = importer.get_import_summary()
        
        # Fetch current prices for all imported stocks
        print(f"DEBUG: Fetching current prices for imported stocks")
        symbols = list(set([h['symbol'] for h in holdings]))
        stocks_to_update = Stock.objects.filter(symbol__in=symbols)
        
        fetcher = StockPriceFetcher()
        price_result = fetcher.update_stock_prices(stocks_to_update)
        print(f"DEBUG: Price fetch results: {price_result}")
        
        # Display results
        if imported_count > 0:
            messages.success(request, f'Successfully imported {imported_count} new holdings!')
        if updated_count > 0:
            messages.info(request, f'Updated {updated_count} existing holdings.')
        if price_result['updated'] > 0:
            messages.success(request, f'Updated prices for {price_result["updated"]} stocks')
        if price_result['failed'] > 0:
            messages.warning(request, f'Could not fetch prices for {price_result["failed"]} stocks')
        if skipped_count > 0:
            messages.warning(request, f'Skipped {skipped_count} holdings (stocks not found in database).')
        if summary['errors']:
            messages.error(request, f"{len(summary['errors'])} errors occurred during import.")
        
        # Store detailed summary in session for review
        request.session['import_summary'] = summary
        
        return redirect('portfolio:import_summary')
        
    except Exception as e:
        messages.error(request, f'File import failed: {str(e)}')
        return redirect('portfolio:import_portfolio')


def handle_image_import(request):
    """Handle portfolio import from images (screenshots)"""
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile
    from django.conf import settings
    import os
    from .image_processor import PortfolioImageProcessor
    
    if 'portfolio_image' not in request.FILES:
        messages.error(request, 'No image file uploaded')
        return redirect('portfolio:import_portfolio')
    
    image_file = request.FILES['portfolio_image']
    use_ai = request.POST.get('use_ai_extraction') == 'on'
    
    # Show progress message
    if use_ai:
        messages.info(request, '🤖 Extracting holdings from image using AI... This may take 10-20 seconds.')
    else:
        messages.info(request, '📸 Extracting holdings from image using OCR... Please wait.')
    
    # Save uploaded image temporarily
    image_path = default_storage.save(f'temp/{image_file.name}', ContentFile(image_file.read()))
    full_image_path = os.path.join(settings.MEDIA_ROOT, image_path)
    
    try:
        # Process image
        processor = PortfolioImageProcessor()
        
        if use_ai:
            openai_key = getattr(settings, 'OPENAI_API_KEY', None)
            gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
            
            if openai_key or gemini_key:
                result = processor.extract_with_ai(full_image_path, openai_key, gemini_key)
                # Check which method was used
                method = result.get('method', '')
                if method == 'gemini_vision' and result.get('success'):
                    messages.info(request, 'Used Google Gemini AI for extraction.')
                elif method == 'ocr' and result.get('success'):
                    messages.info(request, 'AI extraction unavailable (rate limit), used OCR instead.')
            else:
                messages.warning(request, 'No AI API key configured. Using OCR extraction.')
                result = processor.extract_holdings_from_image(full_image_path)
        else:
            result = processor.extract_holdings_from_image(full_image_path)
        
        if not result['success']:
            error_msg = result.get('error', 'Unknown error')
            if 'rate limit' in error_msg.lower():
                messages.warning(request, f"OpenAI rate limit reached. Please try again later or uncheck 'Use AI' to use OCR instead.")
            else:
                messages.error(request, f"Image processing failed: {error_msg}")
            return redirect('portfolio:import_portfolio')
        
        holdings_data = result['holdings']
        
        if not holdings_data:
            messages.warning(request, 'No holdings detected in the image. Please try with a clearer screenshot.')
            return redirect('portfolio:import_portfolio')
        
        # Get or create portfolio
        portfolio, created = UserPortfolio.objects.get_or_create(user=get_default_user())
        
        # Check if user wants to replace existing holdings
        replace_existing = request.POST.get('replace_existing') == 'on'
        
        if replace_existing:
            # Delete all existing holdings
            deleted_count = portfolio.holdings.count()
            portfolio.holdings.all().delete()
            messages.info(request, f'Cleared {deleted_count} existing holdings before import')
        
        # Import holdings
        success_count = 0
        skip_count = 0
        errors = []
        warnings = []
        
        for holding_data in holdings_data:
            try:
                symbol = holding_data.get('symbol', '').upper()
                quantity = int(holding_data.get('quantity', 0))
                avg_price = Decimal(str(holding_data.get('avg_price', 0)))
                
                if not symbol or quantity <= 0 or avg_price <= 0:
                    warnings.append(f"Skipped incomplete data: {holding_data}")
                    skip_count += 1
                    continue
                
                # Get or create stock
                stock, stock_created = Stock.objects.get_or_create(
                    symbol=symbol,
                    defaults={
                        'company_name': symbol,
                        'sector': 'Unknown'
                    }
                )
                
                if not replace_existing:
                    # Check if holding exists (only if not replacing)
                    existing_holding = PortfolioHolding.objects.filter(
                        portfolio=portfolio,
                        stock=stock
                    ).first()
                    
                    if existing_holding:
                        # Update existing by adding quantities
                        total_shares = existing_holding.quantity + quantity
                        total_investment = (
                            existing_holding.quantity * existing_holding.average_price +
                            quantity * avg_price
                        )
                        new_average_price = total_investment / total_shares
                        
                        existing_holding.quantity = total_shares
                        existing_holding.average_price = new_average_price
                        existing_holding.notes = f"{existing_holding.notes}\nImported from image: {quantity} @ ₹{avg_price}".strip()
                        existing_holding.save()
                        success_count += 1
                        continue
                
                # Create new holding (either replace mode or no existing holding)
                PortfolioHolding.objects.create(
                    portfolio=portfolio,
                    stock=stock,
                    quantity=quantity,
                    average_price=avg_price,
                    purchase_date=date.today(),
                    notes="Imported from portfolio screenshot"
                )
                
                success_count += 1
                
            except Exception as e:
                errors.append(f"Error processing {holding_data.get('symbol', 'unknown')}: {str(e)}")
                skip_count += 1
        
        # Store summary in session
        summary = {
            'success_count': success_count,
            'skip_count': skip_count,
            'error_count': len(errors),
            'warning_count': len(warnings),
            'errors': errors,
            'warnings': warnings,
            'detected_broker': result.get('detected_broker'),
            'extraction_method': result.get('method', 'ocr')
        }
        
        request.session['import_summary'] = summary
        
        # Fetch current prices for imported stocks
        symbols = [h['symbol'] for h in holdings_data if h.get('symbol')]
        unique_symbols = list(set(symbols))
        stocks_to_update = Stock.objects.filter(symbol__in=unique_symbols)
        
        fetcher = StockPriceFetcher()
        price_result = fetcher.update_stock_prices(stocks_to_update)
        
        messages.success(request, f'Successfully imported {success_count} holdings from image!')
        if price_result['updated'] > 0:
            messages.success(request, f'Updated prices for {price_result["updated"]} stocks')
        if skip_count > 0:
            messages.warning(request, f'{skip_count} holdings were skipped')
        
        return redirect('portfolio:import_summary')
        
    except Exception as e:
        messages.error(request, f'Error processing image: {str(e)}')
        return redirect('portfolio:import_portfolio')
        
    finally:
        # Clean up temporary file
        if os.path.exists(full_image_path):
            os.remove(full_image_path)


def handle_broker_import(request):
    """Handle broker API import (future implementation)"""
    broker = request.POST.get('broker')
    api_key = request.POST.get('api_key')
    
    messages.info(request, f'Broker API integration for {broker} is coming soon!')
    messages.info(request, 'For now, please export your holdings as CSV from your broker and upload it.')
    return redirect('portfolio:import_portfolio')


def import_summary(request):
    """Show import summary and results"""
    summary = request.session.get('import_summary', {})
    
    if not summary:
        messages.warning(request, 'No import summary available')
        return redirect('portfolio:import_portfolio')
    
    # Clear summary from session
    if 'import_summary' in request.session:
        del request.session['import_summary']
    
    return render(request, 'portfolio/import_summary.html', {
        'summary': summary
    })


def holding_detail(request, holding_id):
    """Detailed view of a specific holding"""
    holding = get_object_or_404(
        PortfolioHolding.objects.select_related('stock', 'portfolio'),
        id=holding_id,
        portfolio__user=get_default_user()
    )
    
    # Get recommendations for this holding
    recommendations = PersonalizedRecommendation.objects.filter(
        holding=holding,
        is_active=True
    ).order_by('-created_at')[:5]
    
    # Get recent news for this stock
    recent_news = NewsArticle.objects.filter(
        mentioned_stocks=holding.stock
    ).order_by('-published_at')[:10]
    
    # Calculate holding metrics
    metrics = {
        'total_investment': holding.total_value,
        'current_value': holding.current_value,
        'profit_loss': holding.pnl,
        'return_percent': holding.pnl_percentage,
        'is_profitable': holding.is_profitable,
        'current_price': holding.stock.current_price or holding.average_price,
        'average_price': holding.average_price,
        'quantity': holding.quantity,
    }
    
    context = {
        'holding': holding,
        'recommendations': recommendations,
        'recent_news': recent_news,
        'metrics': metrics,
    }
    
    return render(request, 'portfolio/holding_detail.html', context)


def download_sample_csv(request):
    """Download sample CSV template for portfolio import"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="portfolio_sample.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['symbol', 'quantity', 'price', 'purchase_date', 'notes'])
    writer.writerow(['RELIANCE', '10', '2450.50', '2024-01-15', 'Long term investment'])
    writer.writerow(['TCS', '5', '3850.00', '2024-02-20', 'IT sector exposure'])
    writer.writerow(['HDFCBANK', '15', '1650.75', '2024-03-10', 'Banking sector'])
    
    return response


def refresh_stock_prices(request):
    """Manually refresh stock prices for portfolio holdings"""
    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX request - start async task
            task_id = str(uuid.uuid4())
            
            try:
                portfolio = get_object_or_404(UserPortfolio, user=get_default_user())
                stock_ids = portfolio.holdings.values_list('stock_id', flat=True).distinct()
                stocks = Stock.objects.filter(id__in=stock_ids)
                
                # Create task
                TaskProgress.create_task(task_id, 'refresh_prices', len(stocks))
                
                # Start processing in background (simulated with immediate execution)
                fetcher = StockPriceFetcher()
                
                updated = 0
                failed = 0
                for i, stock in enumerate(stocks):
                    TaskProgress.update_progress(
                        task_id, 
                        int((i + 1) / len(stocks) * 100),
                        stock.symbol,
                        f'Fetching price for {stock.symbol}...'
                    )
                    
                    result = fetcher.fetch_price(stock.symbol)
                    if result['success']:
                        stock.current_price = result['current_price']
                        stock.price_updated_at = result['timestamp']
                        stock.save(update_fields=['current_price', 'price_updated_at'])
                        updated += 1
                    else:
                        failed += 1
                
                TaskProgress.complete_task(task_id, result={'updated': updated, 'failed': failed})
                
                return JsonResponse({
                    'success': True,
                    'task_id': task_id,
                    'message': 'Price refresh started'
                })
            
            except Exception as e:
                TaskProgress.complete_task(task_id, error=str(e))
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=500)
        else:
            # Regular form POST - show info message and redirect
            messages.info(request, 'Refreshing stock prices in background. You can continue working...')
            
            try:
                portfolio = get_object_or_404(UserPortfolio, user=get_default_user())
                stock_ids = portfolio.holdings.values_list('stock_id', flat=True).distinct()
                stocks = Stock.objects.filter(id__in=stock_ids)
                
                fetcher = StockPriceFetcher()
                result = fetcher.update_stock_prices(stocks)
                
                if result['updated'] > 0:
                    messages.success(request, f'Successfully updated prices for {result["updated"]} stocks!')
                if result['failed'] > 0:
                    messages.warning(request, f'Could not fetch prices for {result["failed"]} stocks.')
                if result['total'] == 0:
                    messages.info(request, 'No stocks found in your portfolio to update.')
            
            except Exception as e:
                messages.error(request, f'Error refreshing prices: {str(e)}')
    
    return redirect('portfolio:dashboard')


def analyze_portfolio(request):
    """AI-powered comprehensive portfolio analysis"""
    from .portfolio_analyzer import PortfolioAnalyzer
    
    if request.method == 'POST':
        # Show info message immediately
        messages.info(request, '🤖 AI analysis started! This may take 10-30 seconds. You can continue working...')
        
        try:
            # Get portfolio
            portfolio = get_object_or_404(UserPortfolio, user=get_default_user())
            
            # Get all holdings
            holdings = portfolio.holdings.select_related('stock').all()
            
            if not holdings.exists():
                messages.warning(request, 'No holdings found to analyze. Please add stocks to your portfolio first.')
                return redirect('portfolio:dashboard')
            
            # Perform analysis
            analyzer = PortfolioAnalyzer()
            analysis_result = analyzer.analyze_portfolio(holdings)
            
            # Store in session for display
            request.session['portfolio_analysis'] = {
                'analyzed_at': analysis_result['analyzed_at'].isoformat(),
                'holdings_analysis': analysis_result['holdings_analysis'],
                'portfolio_summary': analysis_result['portfolio_summary'],
            }
            
            messages.success(
                request,
                f'✅ Successfully analyzed {len(analysis_result["holdings_analysis"])} holdings!'
            )
            
            return redirect('portfolio:analysis_results')
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error analyzing portfolio: {str(e)}')
            return redirect('portfolio:dashboard')
    
    return redirect('portfolio:dashboard')


def analysis_results(request):
    """Display portfolio analysis results"""
    analysis = request.session.get('portfolio_analysis')
    
    if not analysis:
        messages.warning(request, 'No analysis results available. Please run analysis first.')
        return redirect('portfolio:dashboard')
    
    context = {
        'analysis': analysis,
    }
    
    return render(request, 'portfolio/analysis_results.html', context)
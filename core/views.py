from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib import messages

from .models import AnalysisResult, Madhab
from .classifier import classify, IngredientResult, ClassificationReport, STATUS_PRIORITY, IngredientStatus
from .barcode import fetch_by_barcode


def index(request):
    recent = AnalysisResult.objects.order_by('-created_at')[:5]
    return render(request, 'core/index.html', {
        'madhab_choices': Madhab.choices,
        'recent': recent,
    })


@require_http_methods(["POST"])
def analyze_text(request):
    raw_text = request.POST.get('ingredients', '').strip()
    madhab = request.POST.get('madhab', Madhab.HANAFI)

    if not raw_text:
        messages.error(request, "Please enter some ingredients.")
        return render(request, 'core/index.html', {'madhab_choices': Madhab.choices})

    report = classify(raw_text, madhab)
    result = _save_result(raw_text, madhab, report, product_name=request.POST.get('product_name', ''))

    return render(request, 'core/result.html', {
        'result': result,
        'report': report,
        'madhab': madhab,
    })


@require_http_methods(["POST"])
def analyze_barcode(request):
    barcode = request.POST.get('barcode', '').strip()
    madhab = request.POST.get('madhab', Madhab.HANAFI)

    if not barcode:
        messages.error(request, "Please enter a barcode.")
        return render(request, 'core/index.html', {'madhab_choices': Madhab.choices})

    product = fetch_by_barcode(barcode)

    if not product['found']:
        messages.error(request, f"Barcode not found: {product.get('error', 'Unknown error')}")
        return render(request, 'core/index.html', {'madhab_choices': Madhab.choices})

    ingredients_text = product['ingredients_text']
    if not ingredients_text:
        messages.warning(request, f"Product '{product['product_name']}' found but has no ingredient list.")
        return render(request, 'core/index.html', {'madhab_choices': Madhab.choices})

    report = classify(ingredients_text, madhab)
    result = _save_result(
        ingredients_text, madhab, report,
        product_name=product['product_name'],
        barcode=barcode,
    )

    return render(request, 'core/result.html', {
        'result': result,
        'report': report,
        'madhab': madhab,
        'product': product,
    })


@require_http_methods(["POST"])
def analyze_image(request):
    madhab = request.POST.get('madhab', Madhab.HANAFI)
    image = request.FILES.get('image')

    if not image:
        messages.error(request, "Please upload an image.")
        return render(request, 'core/index.html', {'madhab_choices': Madhab.choices})

    try:
        from .ocr import extract_and_classify_from_image
        data = extract_and_classify_from_image(image, madhab)
    except ValueError as e:
        messages.error(request, str(e))
        return render(request, 'core/index.html', {'madhab_choices': Madhab.choices})

    ingredients_text = data.get('ingredients_text', '')
    if not ingredients_text:
        messages.error(request, "Could not find an ingredient list in the image. Try a clearer photo.")
        return render(request, 'core/index.html', {'madhab_choices': Madhab.choices})

    results = []
    for item in data.get('results', []):
        results.append(IngredientResult(
            original=item['ingredient'],
            matched_name=item['ingredient'],
            status=item['status'],
            source=item['reason'],
            source_url='',
            notes='Classified by AI vision — verify independently.',
            ai_classified=True,
        ))

    overall = max(results, key=lambda r: STATUS_PRIORITY.get(r.status, 0)).status if results else IngredientStatus.QUESTIONABLE

    report = ClassificationReport(
        overall_status=overall,
        ingredient_results=results,
        ai_used=True,
    )

    result = _save_result(ingredients_text, madhab, report)

    return render(request, 'core/result.html', {
        'result': result,
        'report': report,
        'madhab': madhab,
        'ocr_text': ingredients_text,
    })


def result_detail(request, pk):
    result = get_object_or_404(AnalysisResult, pk=pk)
    return render(request, 'core/result.html', {
        'result': result,
        'ingredient_results': result.ingredient_results,
        'madhab': result.madhab,
    })


def _save_result(raw_text, madhab, report, product_name='', barcode=''):
    return AnalysisResult.objects.create(
        raw_text=raw_text,
        barcode=barcode,
        product_name=product_name,
        madhab=madhab,
        overall_status=report.overall_status,
        ingredient_results=[
            {
                'original': r.original,
                'matched_name': r.matched_name,
                'status': r.status,
                'source': r.source,
                'source_url': r.source_url,
                'notes': r.notes,
                'ai_classified': r.ai_classified,
            }
            for r in report.ingredient_results
        ],
        unknown_ingredients=report.unknown_ingredients,
        ai_used=report.ai_used,
    )
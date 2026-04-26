from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_http_methods
from django.contrib import messages

from .models import AnalysisResult, Madhab
from .classifier import classify
from .barcode import fetch_by_barcode
from .ocr import extract_text_from_image


def index(request):
    """Main page — text input + barcode + image upload form."""
    recent = AnalysisResult.objects.order_by('-created_at')[:5]
    return render(request, 'core/index.html', {
        'madhab_choices': Madhab.choices,
        'recent': recent,
    })


@require_http_methods(["POST"])
def analyze_text(request):
    """Handle raw ingredient text submission."""
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
    """Fetch product from Open Food Facts, then classify."""
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
    messages.error(request, "Image upload is not available yet.")
    return render(request, 'core/index.html', {'madhab_choices': Madhab.choices})

# @require_http_methods(["POST"])
# def analyze_image(request):
#     """Extract text from uploaded image via OCR, then classify."""
#     madhab = request.POST.get('madhab', Madhab.HANAFI)
#     image = request.FILES.get('image')
#
#     if not image:
#         messages.error(request, "Please upload an image.")
#         return render(request, 'core/index.html', {'madhab_choices': Madhab.choices})
#
#     try:
#         raw_text = extract_text_from_image(image)
#     except ValueError as e:
#         messages.error(request, str(e))
#         return render(request, 'core/index.html', {'madhab_choices': Madhab.choices})
#
#     if not raw_text:
#         messages.error(request, "Could not extract any text from the image. Try a clearer photo.")
#         return render(request, 'core/index.html', {'madhab_choices': Madhab.choices})
#
#     report = classify(raw_text, madhab)
#     result = _save_result(raw_text, madhab, report)
#
#     return render(request, 'core/result.html', {
#         'result': result,
#         'report': report,
#         'madhab': madhab,
#         'ocr_text': raw_text,
#     })


def result_detail(request, pk):
    """View a previously saved analysis."""
    result = get_object_or_404(AnalysisResult, pk=pk)
    return render(request, 'core/result.html', {
        'result': result,
        'ingredient_results': result.ingredient_results,
        'madhab': result.madhab,
    })


# ── helpers ──────────────────────────────────────────────────────────────────

def _save_result(raw_text, madhab, report, product_name='', barcode=''):
    """Persist analysis to DB and return the saved instance."""
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
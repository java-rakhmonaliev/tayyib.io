from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status

from .models import AnalysisResult, Madhab
from .classifier import classify, IngredientResult, ClassificationReport, STATUS_PRIORITY, IngredientStatus
from .barcode import fetch_by_barcode
from .serializers import AnalysisResultSerializer


@api_view(['POST'])
def api_analyze_text(request):
    raw_text = request.data.get('ingredients', '').strip()
    madhab = request.data.get('madhab', Madhab.HANAFI)

    if not raw_text:
        return Response({'error': 'ingredients field is required.'}, status=status.HTTP_400_BAD_REQUEST)

    if madhab not in [Madhab.HANAFI, Madhab.MALIKI, Madhab.SHAFII, Madhab.HANBALI]:
        return Response({'error': 'madhab must be hanafi, maliki, shafii or hanbali.'}, status=status.HTTP_400_BAD_REQUEST)

    report = classify(raw_text, madhab)
    result = _save_result(raw_text, madhab, report, product_name=request.data.get('product_name', ''))

    return Response(_build_response(result, report), status=status.HTTP_200_OK)


@api_view(['POST'])
def api_analyze_barcode(request):
    barcode = request.data.get('barcode', '').strip()
    madhab = request.data.get('madhab', Madhab.HANAFI)

    if not barcode:
        return Response({'error': 'barcode field is required.'}, status=status.HTTP_400_BAD_REQUEST)

    product = fetch_by_barcode(barcode)

    if not product['found']:
        return Response({'error': product.get('error', 'Product not found.')}, status=status.HTTP_404_NOT_FOUND)

    ingredients_text = product['ingredients_text']
    if not ingredients_text:
        return Response({'error': 'Product found but has no ingredient list.'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    report = classify(ingredients_text, madhab)
    result = _save_result(
        ingredients_text, madhab, report,
        product_name=product['product_name'],
        barcode=barcode,
    )

    return Response({
        **_build_response(result, report),
        'product': {
            'name': product['product_name'],
            'brands': product['brands'],
            'image_url': product['image_url'],
            'barcode': barcode,
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def api_analyze_image(request):
    madhab = request.data.get('madhab', Madhab.HANAFI)
    image = request.FILES.get('image')

    if not image:
        return Response({'error': 'image file is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        from .ocr import extract_and_classify_from_image
        data = extract_and_classify_from_image(image, madhab)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    ingredients_text = data.get('ingredients_text', '')
    has_halal_logo = data.get('has_halal_logo', False)
    halal_logo_name = data.get('halal_logo_name', None)

    if not ingredients_text:
        return Response({'error': 'Could not find an ingredient list in the image.'}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

    if has_halal_logo:
        results = [
            IngredientResult(
                original=item['ingredient'],
                matched_name=item['ingredient'],
                status='halal',
                source=f'Product is certified halal ({halal_logo_name or "logo detected"}).',
                source_url='',
                notes='Classified by AI vision.',
                ai_classified=True,
            )
            for item in data.get('results', [])
        ]
        overall = IngredientStatus.HALAL
    else:
        results = [
            IngredientResult(
                original=item['ingredient'],
                matched_name=item['ingredient'],
                status=item['status'],
                source=item['reason'],
                source_url='',
                notes='Classified by AI vision.',
                ai_classified=True,
            )
            for item in data.get('results', [])
        ]
        overall = max(results, key=lambda r: STATUS_PRIORITY.get(r.status, 0)).status if results else IngredientStatus.QUESTIONABLE

    report = ClassificationReport(overall_status=overall, ingredient_results=results, ai_used=True)
    result = _save_result(ingredients_text, madhab, report)

    return Response({
        **_build_response(result, report),
        'has_halal_logo': has_halal_logo,
        'halal_logo_name': halal_logo_name,
        'extracted_text': ingredients_text,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def api_results(request):
    results = AnalysisResult.objects.order_by('-created_at')[:20]
    serializer = AnalysisResultSerializer(results, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def api_result_detail(request, pk):
    try:
        result = AnalysisResult.objects.get(pk=pk)
    except AnalysisResult.DoesNotExist:
        return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
    serializer = AnalysisResultSerializer(result)
    return Response(serializer.data)


# ── helpers ──────────────────────────────────────────────────────────────────

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


def _build_response(result, report):
    return {
        'id': result.id,
        'overall_status': report.overall_status,
        'madhab': result.madhab,
        'product_name': result.product_name,
        'ai_used': report.ai_used,
        'ingredients': [
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
        'unknown_ingredients': report.unknown_ingredients,
    }

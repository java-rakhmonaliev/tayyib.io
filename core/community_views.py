from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import ProductCommunityReport, ProductCommunityScore, VoteChoice


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_report(request):
    barcode = request.data.get('barcode', '').strip()
    vote = request.data.get('vote', '').strip()
    product_name = request.data.get('product_name', '').strip()
    note = request.data.get('note', '').strip()
    madhab = request.data.get('madhab', 'hanafi').strip()
    country = request.data.get('country', '').strip()

    if not barcode:
        return Response({'error': 'barcode is required.'}, status=status.HTTP_400_BAD_REQUEST)

    valid_votes = [v.value for v in VoteChoice]
    if vote not in valid_votes:
        return Response({'error': f'vote must be one of {valid_votes}'}, status=status.HTTP_400_BAD_REQUEST)

    # One vote per user per product — update if exists
    report, created = ProductCommunityReport.objects.update_or_create(
        user=request.user,
        barcode=barcode,
        defaults={
            'vote': vote,
            'product_name': product_name,
            'note': note,
            'madhab': madhab,
            'country': country,
        }
    )

    # Update aggregated score
    _update_score(barcode, product_name)

    return Response({
        'message': 'Vote submitted successfully.',
        'vote': vote,
        'created': created,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_score(request, barcode):
    try:
        score = ProductCommunityScore.objects.get(barcode=barcode)
        return Response({
            'barcode': score.barcode,
            'product_name': score.product_name,
            'community_verdict': score.community_verdict,
            'total_votes': score.total_votes,
            'confirmed_halal_count': score.confirmed_halal_count,
            'found_issue_count': score.found_issue_count,
            'not_sure_count': score.not_sure_count,
            'last_updated': score.last_updated,
        })
    except ProductCommunityScore.DoesNotExist:
        return Response({
            'barcode': barcode,
            'community_verdict': 'unverified',
            'total_votes': 0,
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_vote(request, barcode):
    try:
        report = ProductCommunityReport.objects.get(user=request.user, barcode=barcode)
        return Response({'vote': report.vote, 'note': report.note})
    except ProductCommunityReport.DoesNotExist:
        return Response({'vote': None})


def _update_score(barcode, product_name=''):
    reports = ProductCommunityReport.objects.filter(barcode=barcode)
    score, _ = ProductCommunityScore.objects.get_or_create(barcode=barcode)

    score.product_name = product_name or score.product_name
    score.confirmed_halal_count = reports.filter(vote='confirmed_halal').count()
    score.found_issue_count = reports.filter(vote='found_issue').count()
    score.not_sure_count = reports.filter(vote='not_sure').count()
    score.recalculate()
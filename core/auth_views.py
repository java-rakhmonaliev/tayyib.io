from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get('username', '').strip()
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '').strip()
    madhab = request.data.get('madhab', 'hanafi').strip()

    if not username or not email or not password:
        return Response({'error': 'username, email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    if len(password) < 8:
        return Response({'error': 'Password must be at least 8 characters.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already taken.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=email).exists():
        return Response({'error': 'Email already registered.'}, status=status.HTTP_400_BAD_REQUEST)

    user = User.objects.create_user(username=username, email=email, password=password)

    # Save madhab in profile
    UserProfile.objects.create(user=user, madhab=madhab)

    tokens = get_tokens_for_user(user)
    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'madhab': madhab,
        },
        **tokens,
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    username = request.data.get('username', '').strip()
    password = request.data.get('password', '').strip()

    if not username or not password:
        return Response({'error': 'username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    from django.contrib.auth import authenticate
    user = authenticate(username=username, password=password)

    if not user:
        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

    profile, _ = UserProfile.objects.get_or_create(user=user)
    tokens = get_tokens_for_user(user)

    return Response({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'madhab': profile.madhab,
        },
        **tokens,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    user = request.user
    prof, _ = UserProfile.objects.get_or_create(user=user)
    return Response({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'madhab': prof.madhab,
        'country': prof.country,
        'total_scans': prof.total_scans,
        'joined': user.date_joined,
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    prof, _ = UserProfile.objects.get_or_create(user=request.user)
    madhab = request.data.get('madhab')
    country = request.data.get('country')

    if madhab:
        valid = ['hanafi', 'maliki', 'shafii', 'hanbali']
        if madhab not in valid:
            return Response({'error': f'madhab must be one of {valid}'}, status=status.HTTP_400_BAD_REQUEST)
        prof.madhab = madhab

    if country:
        prof.country = country

    prof.save()
    return Response({
        'madhab': prof.madhab,
        'country': prof.country,
    })


from .models import UserProfile

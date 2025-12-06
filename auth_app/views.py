from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import build_google_auth_url, exchange_code_for_token, fetch_userinfo
from .models import User
from .serializers import UserSerializer

class GoogleAuthURLView(APIView):
    def get(self, request):
        url = build_google_auth_url()
        # Option A: redirect
        if request.query_params.get("redirect", "1") == "1":
            return Response({"redirect_url": url}, status=status.HTTP_200_OK)
        return Response({"google_auth_url": url}, status=status.HTTP_200_OK)

class GoogleCallbackView(APIView):
    def get(self, request):
        code = request.query_params.get("code")
        if not code:
            return Response({"detail": "Missing code"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token_resp = exchange_code_for_token(code)
            access_token = token_resp.get("access_token")
            if not access_token:
                return Response({"detail": "Invalid code"}, status=status.HTTP_401_UNAUTHORIZED)
            userinfo = fetch_userinfo(access_token)
            google_id = userinfo.get("sub") or userinfo.get("id")
            email = userinfo.get("email")
            name = userinfo.get("name", "")
            picture = userinfo.get("picture", "")

            user, created = User.objects.update_or_create(
                google_id=google_id,
                defaults={"email": email, "name": name, "picture": picture},
            )
            serializer = UserSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


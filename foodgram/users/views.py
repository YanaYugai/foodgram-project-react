from django.shortcuts import render
from rest_framework import filters, mixins, viewsets
from django.contrib.auth import get_user_model
from rest_framework import generics, status, viewsets
from users.serializers import FollowsSerializer, FollowResultSerializer
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from api.models import Follow
from django.http import Http404
from api.paginators import LimitPagination
from rest_framework.permissions import IsAuthenticated
from api.utils import get_obj
User = get_user_model()


class FollowApiView(mixins.CreateModelMixin, mixins.DestroyModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = FollowsSerializer
    pagination_class = LimitPagination
    permission_classes = (IsAuthenticated, )

    def get_author(self, user_id):
        try:
            author = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise Http404(
                "Не найден пользователь или неверный запрос!",
            )
        return author

    def create(self, request, user_id):
        serializer = self.get_serializer(data={'user': request.user.id, 'author': get_obj(user_id, User).pk})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        author = User.objects.get(pk=serializer.validated_data['author'].id)
        result = FollowResultSerializer(author, context={'request': request})
        return Response(result.data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        author = get_obj(self.kwargs['user_id'], User)
        if Follow.objects.filter(user=request.user.id, author=author.id).exists():
            self.perform_destroy(Follow.objects.get(user=request.user.id, author=author.id))
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = User.objects.filter(following__user=request.user.id)
        pages = self.paginate_queryset(queryset)
        serializer = FollowResultSerializer(pages, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

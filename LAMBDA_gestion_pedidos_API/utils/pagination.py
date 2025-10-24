from rest_framework.pagination import LimitOffsetPagination


class PaginacionEstandar(LimitOffsetPagination):
    default_limit = 20
    max_limit = 100


class PaginacionGrande(LimitOffsetPagination):
    default_limit = 50
    max_limit = 200


class PaginacionPequena(LimitOffsetPagination):
    default_limit = 10
    max_limit = 50

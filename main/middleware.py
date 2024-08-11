from django.http import JsonResponse
from .models import Analysis


class AnalysisStatusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/get_analysis_status/"):
            analysis_id = request.path.split("/")[-1]
            if analysis_id.isdigit():
                try:
                    analysis = Analysis.objects.get(
                        id=int(analysis_id), user=request.user
                    )
                    return self.get_response(request)
                except Analysis.DoesNotExist:
                    return JsonResponse({"error": "Analysis not found"}, status=404)
            else:
                return JsonResponse({"error": "Invalid analysis ID"}, status=400)
        return self.get_response(request)

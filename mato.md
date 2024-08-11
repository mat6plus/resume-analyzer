@login_required
@csrf_exempt
@require_POST
def stop_analysis(request, analysis_id):
    try:
        analysis = Analysis.objects.get(id=analysis_id, user=request.user)
        if analysis.status == "in_progress":
            analysis.status = "stopped"
            analysis.save()
            return JsonResponse({"status": "stopped"})
        else:
            return JsonResponse({"status": "not_in_progress"}, status=400)
    except Analysis.DoesNotExist:
        print(f"Analysis not found for analysis_id: {analysis_id}")
        return JsonResponse({"error": "Analysis not found"}, status=404)
    except Exception as e:
        print(f"Error in stop_analysis view: {str(e)}")
        return JsonResponse({"error": "An unexpected error occurred"}, status=500)
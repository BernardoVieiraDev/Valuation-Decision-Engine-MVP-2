from django.shortcuts import render

def panorama_view(request):
    """
    Renderiza o template do Panorama. 
    Os dados são carregados de forma assíncrona pelo client-side via FastAPI (/api/market/*)
    """
    return render(request, "panorama/panorama.html")
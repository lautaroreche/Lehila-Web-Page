import io
from django.shortcuts import render
import pandas as pd
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST


def home(request):
    context = {} 
    return render(request, 'index.html', context)


@require_POST
def organize(request):
    file = request.FILES.get("file")
    if not file:
        return JsonResponse({"ok": False, "error": "No se recibió el archivo"}, status=400)

    file_name = (file.name or "").lower()
    if not (file_name.endswith(".xlsx") or file_name.endswith(".xls")):
        return JsonResponse({"ok": False, "error": "Solo se aceptan archivos Excel (.xlsx o .xls)."}, status=400)

    try:
        df = pd.read_excel(file, header=None)
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"No se pudo leer el archivo: {e}"}, status=400)

    if df.empty:
        return JsonResponse({"ok": False, "error": "El archivo está vacío."}, status=400)

    # Convertir la primera columna a lista limpia
    col = df.iloc[:, 0].astype(str).str.strip()
    col = col[col.ne("") & col.ne("nan")].tolist()

    if len(col) < 4:
        return JsonResponse({"ok": False, "error": "No hay suficientes datos para formar 4 columnas."}, status=400)

    # Asegurar múltiplo de 4
    remainder = len(col) % 4
    if remainder != 0:
        col += [""] * (4 - remainder)

    # Agrupar cada 4 elementos
    blocks = [col[i:i + 4] for i in range(0, len(col), 4)]
    headers = blocks[0]
    rows = blocks[1:]

    # Crear DataFrame ordenado
    out_df = pd.DataFrame(rows, columns=headers)

    # Guardar a Excel en memoria
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        out_df.to_excel(writer, index=False, sheet_name="Ordenado")
    buf.seek(0)

    # Responder archivo para descargar
    resp = HttpResponse(
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    resp["Content-Disposition"] = f'attachment; filename="{file.name}"'
    return resp

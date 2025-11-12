from django.http import JsonResponse
@require_http_methods(['GET'])
def consultas_general_test(request):
    """Vista de prueba para POST a REUNE /consultas/general con body fijo."""
    token = request.session.get('redeco_token')
    error = None
    result = None
    if not token:
        error = 'Token no disponible. Genera un token desde la página principal.'
    else:
        body = [
            {
                "InstitucionClave": "Unión de Crédito Integral, S.A. de C.V.",
                "Sector": "Uniones de crédito",
                "ConsultasTrim": 3,
                "NumConsultas": 1,
                "ConsultasFolio": "250701",
                "ConsultasEstatusCon": 2,
                "ConsultasFecAten": "07/07/2025",
                "EstadosId": 9,
                "ConsultasFecRecepcion": "07/07/2025",
                "MediosId": 4,
                "Producto": "028212771385",
                "CausaId": "1211",
                "ConsultasCP": 11550,
                "ConsultasMpioId": 16,
                "ConsultasLocId": 9,
                "ConsultasColId": 2784,
                "ConsultascatnivelatenId": 1,
                "ConsultasPori": "NO"
            },
            # ... puedes agregar más dicts aquí para pruebas ...
        ]
        try:
            result = services.post_consultas_general(token, body)
        except services.RedeCoAPIError as exc:
            error = str(exc)
    return render(request, 'consultas_general_test.html', {'token': token, 'result': result, 'error': error})
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from . import services


@require_http_methods(['GET', 'POST'])
def index(request):
    """Render the landing page / demo frontend view and handle token retrieval."""
    example = {
        'username': 'UCISA',
        'password': 'Ucisa.condusef.api_24',
    }

    token = request.session.get('redeco_token')
    error = None

    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = (request.POST.get('password') or '').strip()

        # validate required fields
        if not username or not password:
            error = 'Usuario y contraseña son obligatorios.'
            token = None
        else:
            try:
                token = services.get_token(username, password)
                # Save token in session for later requests
                request.session['redeco_token'] = token
            except services.RedeCoAPIError as exc:
                # show only concise message extracted from API
                error = str(exc)
                token = None

    return render(request, 'index.html', {'example': example, 'token': token, 'error': error})


@require_http_methods(['GET'])
def catalogs_medios(request):
    """Fetch and display medios de recepción catalog (public endpoint, no token required)."""
    data = None
    error = None

    try:
        # Call the public endpoint
        response = services.call_public_endpoint('catalogos/medio-recepcion')
        data = response
    except services.RedeCoAPIError as exc:
        error = str(exc)

    context = {
        'data': data,
        'error': error,
        'catalog_name': 'Medios de Recepción',
    }
    return render(request, 'catalogs_medios.html', context)


@require_http_methods(['GET'])
def catalogs_niveles_atencion(request):
    """Fetch and display niveles de atención catalog (public endpoint, no token required)."""
    data = None
    error = None

    try:
        # Call the public endpoint
        response = services.call_public_endpoint('catalogos/niveles-atencion')
        data = response
    except services.RedeCoAPIError as exc:
        error = str(exc)

    context = {
        'data': data,
        'error': error,
        'catalog_name': 'Niveles de Atención',
    }
    return render(request, 'catalogs_niveles_atencion.html', context)


@require_http_methods(['GET'])
def catalogs_estados(request):
    """Fetch and display estados catalog (public endpoint, no token required)."""
    data = None
    error = None

    try:
        # Call the public endpoint
        response = services.call_public_endpoint('sepomex/estados/')
        data = response
    except services.RedeCoAPIError as exc:
        error = str(exc)

    context = {
        'data': data,
        'error': error,
        'catalog_name': 'Estados',
    }
    return render(request, 'catalogs_estados.html', context)


@require_http_methods(['GET'])
def catalogs_codigos_postales(request):
    """Fetch and display códigos postales catalog (public endpoint, requires estado_id parameter)."""
    data = None
    error = None
    estados = None
    selected_estado_id = request.GET.get('estado_id')

    # Always fetch the list of states to show in the dropdown
    try:
        estados_response = services.call_public_endpoint('sepomex/estados/')
        estados = estados_response.get('estados', [])
    except services.RedeCoAPIError as exc:
        error = f"Error al cargar estados: {str(exc)}"

    # If an estado_id is selected, fetch the postal codes for that state
    if selected_estado_id:
        try:
            response = services.call_public_endpoint(
                'sepomex/codigos-postales/',
                params={'estado_id': selected_estado_id}
            )
            data = response
        except services.RedeCoAPIError as exc:
            error = str(exc)

    context = {
        'data': data,
        'error': error,
        'estados': estados,
        'selected_estado_id': selected_estado_id,
        'catalog_name': 'Códigos Postales',
    }
    return render(request, 'catalogs_codigos_postales.html', context)


@require_http_methods(['GET'])
def catalogs_municipios(request):
    """Fetch and display municipios catalog (public endpoint, requires estado_id and cp parameters)."""
    data = None
    error = None
    estados = None
    selected_estado_id = request.GET.get('estado_id')
    codigo_postal = request.GET.get('cp')

    # Always fetch the list of states to show in the dropdown
    try:
        estados_response = services.call_public_endpoint('sepomex/estados/')
        estados = estados_response.get('estados', [])
    except services.RedeCoAPIError as exc:
        error = f"Error al cargar estados: {str(exc)}"

    # If both estado_id and cp are provided, fetch the municipios
    if selected_estado_id and codigo_postal:
        try:
            response = services.call_public_endpoint(
                'sepomex/municipios/',
                params={'estado_id': selected_estado_id, 'cp': codigo_postal}
            )
            data = response
        except services.RedeCoAPIError as exc:
            error = str(exc)

    context = {
        'data': data,
        'error': error,
        'estados': estados,
        'selected_estado_id': selected_estado_id,
        'codigo_postal': codigo_postal,
        'catalog_name': 'Municipios',
    }
    return render(request, 'catalogs_municipios.html', context)


@require_http_methods(['GET'])
def catalogs_colonias(request):
    """Fetch and display colonias catalog (public endpoint, requires cp parameter)."""
    data = None
    error = None
    codigo_postal = request.GET.get('cp')

    # If cp is provided, fetch the colonias
    if codigo_postal:
        try:
            response = services.call_public_endpoint(
                'sepomex/colonias/',
                params={'cp': codigo_postal}
            )
            data = response
        except services.RedeCoAPIError as exc:
            error = str(exc)

    context = {
        'data': data,
        'error': error,
        'codigo_postal': codigo_postal,
        'catalog_name': 'Colonias',
    }
    return render(request, 'catalogs_colonias.html', context)


@require_http_methods(['GET'])
def catalogs_productos(request):
    """Fetch and display productos catalog (protected endpoint requiring token)."""
    token = request.session.get('redeco_token')
    data = None
    error = None
    raw_response = None

    if not token:
        error = 'Token no disponible. Genera un token desde la página principal.'
    else:
        try:
            response = services.call_protected_endpoint(
                'catalogos/products-list',
                token
            )
            data = response
            # Store raw JSON for the modal
            import json
            raw_response = json.dumps(response, indent=2, ensure_ascii=False)
        except services.RedeCoAPIError as exc:
            error = str(exc)

    context = {
        'token': token,
        'data': data,
        'error': error,
        'raw_response': raw_response,
        'catalog_name': 'Productos',
    }
    return render(request, 'catalogs_productos.html', context)


@require_http_methods(['GET'])
def catalogs_causas(request):
    """Fetch and display causas catalog (protected endpoint requiring token)."""
    token = request.session.get('redeco_token')
    product = request.GET.get('product', '028212721377')  # default product code
    data = None
    error = None

    if not token:
        error = 'Token no disponible. Genera un token desde la página principal.'
    else:
        try:
            # Call the protected endpoint
            # Note: URL in Postman has duplication in path, but we'll use the clean path
            response = services.call_protected_endpoint(
                'catalogos/causas-list/',
                token,
                params={'product': product}
            )
            data = response
        except services.RedeCoAPIError as exc:
            error = str(exc)

    context = {
        'token': token,
        'product': product,
        'data': data,
        'error': error,
    }
    return render(request, 'catalogs_causas.html', context)

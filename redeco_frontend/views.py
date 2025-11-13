from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from functools import wraps
from . import services


def require_token(view_func):
    """Decorator to require a saved redeco_token in session.

    If token not present, redirect to index (login page) and store a
    short message in session to show to the user.
    """
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        token = request.session.get('redeco_token')
        if not token:
            request.session['login_required_message'] = (
                'Debes iniciar sesión antes de acceder a esta página.'
            )
            return redirect('redeco_frontend:index')
        return view_func(request, *args, **kwargs)

    return _wrapped


@require_http_methods(['GET', 'POST'])
def index(request):
    """Render the landing page / demo frontend view and handle token retrieval."""
    example = {
        'username': 'UCISA',
        'password': 'Ucisa.condusef.api_24',
    }

    token = request.session.get('redeco_token')
    error = None
    # If a previous redirect stored a login-required message, show it once
    login_msg = request.session.pop('login_required_message', None)

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

    return render(
        request,
        'index.html',
        {
            'example': example,
            'token': token,
            'error': error,
            'login_msg': login_msg,
        },
    )


@require_http_methods(['GET'])
@require_token
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
@require_token
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
@require_token
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
@require_token
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
@require_token
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
@require_token
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
@require_token
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
@require_token
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


@require_http_methods(['GET', 'POST'])
def reune_consultas(request):
    """Submit consultas to REUNE API (POST to /reune/consultas/general)."""
    import json
    
    token = request.session.get('redeco_token')
    result = None
    error = None
    payload_text = ''
    
    if request.method == 'POST':
        if not token:
            error = 'Token no disponible. Genera un token desde la página principal.'
        else:
            payload_text = request.POST.get('payload', '').strip()
            
            if not payload_text:
                error = 'El payload JSON no puede estar vacío.'
            else:
                try:
                    # Parse JSON payload
                    payload = json.loads(payload_text)
                except json.JSONDecodeError as e:
                    error = f'JSON inválido: {str(e)}'
                else:
                    try:
                        # Call REUNE API
                        result = services.post_reune_consultas_general(token, payload)
                    except services.RedeCoAPIError as exc:
                        error = str(exc)
    
    context = {
        'token': token,
        'result': result,
        'error': error,
        'payload_text': payload_text,
    }
    return render(request, 'reune_consultas.html', context)

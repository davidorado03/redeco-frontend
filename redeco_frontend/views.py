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
            # Save a message to show on the login page and redirect there.
            # Previously this redirected to `index` which is now the protected
            # dashboard; that caused a redirect loop when index required a token.
            request.session['login_required_message'] = (
                'Debes iniciar sesión antes de acceder a esta página.'
            )
            return redirect('redeco_frontend:login')
        return view_func(request, *args, **kwargs)

    return _wrapped


@require_http_methods(['GET'])
@require_token
def index(request):
    """Dashboard page shown after login. Index is protected and requires token."""
    token = request.session.get('redeco_token')
    # simple context: token present
    return render(request, 'index.html', {'token': token})


@require_http_methods(['GET', 'POST'])
def login_view(request):
    """Dedicated login page to obtain and store REDECO token in session."""
    example = {
        'username': 'UCISA',
        'password': 'Ucisa.condusef.api_24',
    }

    error = None
    login_msg = request.session.pop('login_required_message', None)

    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = (request.POST.get('password') or '').strip()

        if not username or not password:
            error = 'Usuario y contraseña son obligatorios.'
        else:
            try:
                token = services.get_token(username, password)
                # Save token and redirect to index
                request.session['redeco_token'] = token
                return redirect('redeco_frontend:index')
            except services.RedeCoAPIError as exc:
                error = str(exc)

    return render(request, 'login.html', {'example': example, 'error': error, 'login_msg': login_msg})


@require_http_methods(['POST'])
def logout_view(request):
    """Logout: remove token from session and redirect to login."""
    request.session.pop('redeco_token', None)
    return redirect('redeco_frontend:login')


@require_http_methods(['GET'])
@require_token
def catalogs_medios(request):
    """Fetch and display medios de recepción catalog (public endpoint, no token required)."""
    data = None
    error = None

    try:
        # Call the public endpoint
        response = services.call_public_endpoint('catalogos/medio-recepcion')
        # Normalizar posibles estructuras
        medios_list = []
        if isinstance(response, dict):
            # Claves comunes observadas
            for key in ('medio', 'medios', 'mediosRecepcion', 'mediosDeRecepcion'):
                val = response.get(key)
                if isinstance(val, list) and val:
                    medios_list = val
                    break
            # A veces viene anidado en 'data'
            if not medios_list and isinstance(response.get('data'), dict):
                nested = response.get('data')
                for key in ('medio', 'medios', 'mediosRecepcion', 'mediosDeRecepcion'):
                    val = nested.get(key)
                    if isinstance(val, list) and val:
                        medios_list = val
                        break
            if not medios_list and isinstance(response.get('data'), list):
                medios_list = response.get('data')
        elif isinstance(response, list):
            medios_list = response

        data = {'medio': medios_list} if medios_list else response
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
            # Normalizar respuesta de productos
            productos = []
            if isinstance(response, dict):
                for key in ('products', 'productos', 'productsList', 'listaProductos'):
                    val = response.get(key)
                    if isinstance(val, list) and val:
                        productos = val
                        break
                if not productos and isinstance(response.get('data'), dict):
                    nested = response.get('data')
                    for key in ('products', 'productos', 'productsList', 'listaProductos'):
                        val = nested.get(key)
                        if isinstance(val, list) and val:
                            productos = val
                            break
                if not productos and isinstance(response.get('data'), list):
                    productos = response.get('data')
            elif isinstance(response, list):
                productos = response
            productos = productos or []
            data = {'products': productos} if productos else response
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
    from django.http import JsonResponse
    
    token = request.session.get('redeco_token')
    product = request.GET.get('product', '028212721377')  # default product code
    data = None
    error = None

    if not token:
        error = 'Token no disponible. Genera un token desde la página principal.'
    else:
        try:
            response = services.call_protected_endpoint(
                'catalogos/causas-list/',
                token,
                params={'product': product}
            )
            causas = []
            if isinstance(response, dict):
                for key in ('causas', 'causasList', 'listaCausas'):
                    val = response.get(key)
                    if isinstance(val, list) and val:
                        causas = val
                        break
                if not causas and isinstance(response.get('data'), dict):
                    nested = response.get('data')
                    for key in ('causas', 'causasList', 'listaCausas'):
                        val = nested.get(key)
                        if isinstance(val, list) and val:
                            causas = val
                            break
                if not causas and isinstance(response.get('data'), list):
                    causas = response.get('data')
            elif isinstance(response, list):
                causas = response
            causas = causas or []
            data = {'causas': causas} if causas else response
        except services.RedeCoAPIError as exc:
            error = str(exc)

    # If AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        if error:
            return JsonResponse({'error': error}, status=400)
        return JsonResponse(data if data else {'causas': []})

    # Otherwise render HTML template
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


@require_http_methods(['GET', 'POST'])
@require_token
def create_queja(request):
    """Create a queja using a friendly form.

    GET: fetch small public catalogs (medios, niveles, estados) to populate selects.
    POST: validate form fields, build the payload expected by the REDECO API and
    call services.create_queja(token, payload).
    """
    import json
    from datetime import datetime

    error = None
    success = None
    payload_sent = None

    # Fetch catalogs for the form selects
    medios = []
    niveles = []
    estados = []
    productos = []

    try:
        med_resp = services.call_public_endpoint('catalogos/medio-recepcion')
        # Normalización ampliada de posibles claves
        if isinstance(med_resp, dict):
            for key in ('medios', 'medio', 'mediosRecepcion', 'mediosDeRecepcion'):
                val = med_resp.get(key)
                if isinstance(val, list) and val:
                    medios = val
                    break
            if not medios and isinstance(med_resp.get('data'), dict):
                nested = med_resp.get('data')
                for key in ('medios', 'medio', 'mediosRecepcion', 'mediosDeRecepcion'):
                    val = nested.get(key)
                    if isinstance(val, list) and val:
                        medios = val
                        break
            if not medios and isinstance(med_resp.get('data'), list):
                medios = med_resp.get('data')
        elif isinstance(med_resp, list):
            medios = med_resp
        medios = medios or []
    except services.RedeCoAPIError:
        # non-fatal: form still rendered without medios
        medios = []

    try:
        niv_resp = services.call_public_endpoint('catalogos/niveles-atencion')
        if isinstance(niv_resp, dict):
            if 'niveles' in niv_resp:
                niveles = niv_resp.get('niveles') or []
            elif 'nivelesDeAtencion' in niv_resp:
                niveles = niv_resp.get('nivelesDeAtencion') or []
            else:
                data_section = niv_resp.get('data')
                if isinstance(data_section, dict):
                    if 'niveles' in data_section:
                        niveles = data_section.get('niveles') or []
                    elif 'nivelesDeAtencion' in data_section:
                        niveles = data_section.get('nivelesDeAtencion') or []
                elif isinstance(data_section, list):
                    niveles = data_section
        elif isinstance(niv_resp, list):
            niveles = niv_resp
        niveles = niveles or []
    except services.RedeCoAPIError:
        niveles = []

    try:
        est_resp = services.call_public_endpoint('sepomex/estados/')
        estados = est_resp.get('estados') if isinstance(est_resp, dict) else []
        estados = estados or []
    except services.RedeCoAPIError:
        estados = []

    token = request.session.get('redeco_token')

    # Productos catalog (protected, requires token)
    if token:
        try:
            prod_resp = services.call_protected_endpoint('catalogos/products-list', token)
            if isinstance(prod_resp, dict):
                for key in ('products', 'productos', 'productsList', 'listaProductos'):
                    val = prod_resp.get(key)
                    if isinstance(val, list) and val:
                        productos = val
                        break
                if not productos and isinstance(prod_resp.get('data'), dict):
                    nested = prod_resp.get('data')
                    for key in ('products', 'productos', 'productsList', 'listaProductos'):
                        val = nested.get(key)
                        if isinstance(val, list) and val:
                            productos = val
                            break
                if not productos and isinstance(prod_resp.get('data'), list):
                    productos = prod_resp.get('data')
            elif isinstance(prod_resp, list):
                productos = prod_resp
        except services.RedeCoAPIError:
            productos = []

    if request.method == 'POST':
        # Collect all form fields per REDECO spec
        no_trim = (request.POST.get('no_trim') or '').strip()
        quejas_num = (request.POST.get('quejas_num') or '1').strip()
        folio = (request.POST.get('folio') or '').strip()
        fecha_recepcion = (request.POST.get('fecha_recepcion') or '').strip()
        medio_id = (request.POST.get('medio_id') or '').strip()
        nivel_id = (request.POST.get('nivel_id') or '').strip()
        producto = (request.POST.get('producto') or '').strip()
        causas_id = (request.POST.get('causas_id') or '').strip()
        pori = (request.POST.get('pori') or '').strip().upper()
        estatus = (request.POST.get('estatus') or '').strip()
        estado_id = (request.POST.get('estado_id') or '').strip()
        municipio = (request.POST.get('municipio') or '').strip()
        localidad = (request.POST.get('localidad') or '').strip()
        colonia = (request.POST.get('colonia') or '').strip()
        cp = (request.POST.get('cp') or '').strip()
        tipo_persona = (request.POST.get('tipo_persona') or '').strip()
        sexo = (request.POST.get('sexo') or '').strip()
        edad = (request.POST.get('edad') or '').strip()
        fecha_resolucion = (request.POST.get('fecha_resolucion') or '').strip()
        fecha_notificacion = (request.POST.get('fecha_notificacion') or '').strip()
        respuesta = (request.POST.get('respuesta') or '').strip()
        num_penal = (request.POST.get('num_penal') or '').strip()
        penalizacion_id = (request.POST.get('penalizacion_id') or '').strip()

        # Enhanced validation per REDECO requirements
        if not all([no_trim, folio, fecha_recepcion, medio_id, nivel_id, producto, causas_id, pori, estatus, estado_id, municipio, colonia, cp, tipo_persona]):
            error = 'Todos los campos marcados como requeridos deben ser completados.'
        elif pori not in ['SI', 'NO']:
            error = 'PORI debe ser "SI" o "NO" (mayúsculas).'
        elif estatus not in ['1', '2']:
            error = 'Estado debe ser 1 (Pendiente) o 2 (Concluido).'
        elif not token:
            error = 'Token no disponible. Genera un token desde la página principal.'
        else:
            # helper to convert html date (YYYY-MM-DD) to dd/mm/YYYY as used in examples
            def _fmt_date(d):
                if not d:
                    return None
                try:
                    # Accept YYYY-MM-DD or already dd/mm/YYYY
                    if '-' in d:
                        dt = datetime.strptime(d, '%Y-%m-%d')
                        return dt.strftime('%d/%m/%Y')
                    # try parsing dd/mm/YYYY
                    dt = datetime.strptime(d, '%d/%m/%Y')
                    return dt.strftime('%d/%m/%Y')
                except Exception:
                    return d

            payload = {
                'QuejasNoTrim': int(no_trim) if no_trim.isdigit() else no_trim,
                'QuejasNum': int(quejas_num) if quejas_num.isdigit() else 1,
                'QuejasFolio': folio,
                'QuejasFecRecepcion': _fmt_date(fecha_recepcion),
                'MedioId': int(medio_id) if medio_id.isdigit() else medio_id,
                'NivelATId': int(nivel_id) if nivel_id.isdigit() else nivel_id,
                'product': producto,
                'CausasId': causas_id,
                'QuejasPORI': pori,
                'QuejasEstatus': int(estatus) if estatus.isdigit() else estatus,
                'EstadosId': int(estado_id) if estado_id.isdigit() else estado_id,
                'QuejasMunId': int(municipio) if municipio.isdigit() else municipio,
                'QuejasLocId': int(localidad) if localidad and localidad.isdigit() else None,
                'QuejasColId': int(colonia) if colonia.isdigit() else colonia,
                'QuejasCP': cp,
                'QuejasTipoPersona': int(tipo_persona) if tipo_persona.isdigit() else tipo_persona,
                'QuejasSexo': sexo if sexo else None,
                'QuejasEdad': int(edad) if edad and edad.isdigit() else None,
                'QuejasFecResolucion': _fmt_date(fecha_resolucion) if fecha_resolucion else None,
                'QuejasFecNotificacion': _fmt_date(fecha_notificacion) if fecha_notificacion else None,
                'QuejasRespuesta': int(respuesta) if respuesta and respuesta.isdigit() else None,
                'QuejasNumPenal': int(num_penal) if num_penal and num_penal.isdigit() else None,
                'PenalizacionId': int(penalizacion_id) if penalizacion_id and penalizacion_id.isdigit() else None,
            }

            # Remove keys with value None to keep payload compact
            payload = {k: v for k, v in payload.items() if v is not None}

            try:
                result = services.create_queja(token, payload)
            except services.RedeCoAPIError as exc:
                error = str(exc)
                payload_sent = json.dumps(payload, ensure_ascii=False, indent=2)
            else:
                success = 'Queja enviada correctamente.'
                payload_sent = json.dumps(payload, ensure_ascii=False, indent=2)

    context = {
        'error': error,
        'success': success,
        'medios': medios,
        'niveles': niveles,
        'estados': estados,
        'productos': productos,
        'payload_text': payload_sent,
    }

    return render(request, 'create_queja.html', context)

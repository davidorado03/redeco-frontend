from django.db import models


class Cliente(models.Model):
    """Modelo para catálogo de clientes."""
    
    TIPO_PERSONA_CHOICES = [
        (1, 'Persona Física'),
        (2, 'Persona Moral'),
    ]
    
    SEXO_CHOICES = [
        ('H', 'Hombre'),
        ('M', 'Mujer'),
    ]
    
    # Campos principales
    nombre = models.CharField(max_length=255, verbose_name='Nombre del cliente')
    rfc = models.CharField(max_length=13, unique=True, verbose_name='RFC')
    tipo_persona = models.IntegerField(choices=TIPO_PERSONA_CHOICES, verbose_name='Tipo de persona')
    
    # Datos geográficos
    estado_id = models.IntegerField(verbose_name='Entidad Federativa (ID)')
    estado_nombre = models.CharField(max_length=100, verbose_name='Entidad Federativa', blank=True)
    codigo_postal = models.CharField(max_length=5, verbose_name='Código Postal')
    municipio_id = models.IntegerField(verbose_name='Municipio (ID)', null=True, blank=True)
    municipio_nombre = models.CharField(max_length=100, verbose_name='Municipio', blank=True)
    colonia_id = models.IntegerField(verbose_name='Colonia (ID)', null=True, blank=True)
    colonia_nombre = models.CharField(max_length=100, verbose_name='Colonia', blank=True)
    localidad = models.CharField(max_length=8, verbose_name='Localidad', blank=True)
    
    # Campos solo para persona física
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, verbose_name='Sexo', null=True, blank=True)
    edad = models.IntegerField(verbose_name='Edad', null=True, blank=True)
    
    # Campos de auditoría
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de actualización')
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.nombre} - {self.rfc}"
    
    def clean(self):
        """Validaciones personalizadas."""
        from django.core.exceptions import ValidationError
        
        # Si es persona física (1), sexo y edad son opcionales pero comunes
        # Si es persona moral (2), sexo y edad deben estar vacíos
        if self.tipo_persona == 2:
            if self.sexo or self.edad:
                raise ValidationError('Las personas morales no pueden tener sexo o edad.')
        
        # Validar edad máximo 3 dígitos
        if self.edad is not None and (self.edad < 0 or self.edad > 999):
            raise ValidationError('La edad debe estar entre 0 y 999.')
        
        # Validar formato de CP (5 dígitos)
        if self.codigo_postal and (len(self.codigo_postal) != 5 or not self.codigo_postal.isdigit()):
            raise ValidationError('El código postal debe tener 5 dígitos.')

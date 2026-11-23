"""
Motor de Triaje Automático con Procesamiento de Lenguaje Natural
Clasifica tickets por categoría y prioridad sin dependencias externas
"""
import re


class MotorTriaje:
    """Motor de clasificación automática de tickets usando NLP básico"""

    def __init__(self):
        self.palabras_clave = {
            'hardware': [
                'pantalla', 'monitor', 'teclado', 'mouse', 'disco', 'ssd',
                'cpu', 'procesador', 'ram', 'memoria', 'placa', 'fuente',
                'ventilador', 'ruido', 'enciende', 'apaga', 'reinicia',
                'equipo', 'computadora', 'laptop', 'pc', 'servidor'
            ],
            'software': [
                'programa', 'aplicacion', 'instalacion', 'actualizacion',
                'error', 'falla', 'crashea', 'congela', 'lento', 'ventana',
                'archivo', 'guardar', 'abrir', 'office', 'excel', 'word',
                'sistema', 'app', 'licencia'
            ],
            'red': [
                'internet', 'wifi', 'conexion', 'red', 'ip', 'router', 'switch',
                'cable', 'navegador', 'pagina', 'servidor', 'acceso', 'dominio',
                'lan', 'ethernet', 'inalambrica'
            ],
            'correo': [
                'correo', 'email', 'outlook', 'gmail', 'mensaje', 'enviar',
                'recibir', 'spam', 'adjunto', 'bandeja', 'contrasena', 'cuenta'
            ],
            'sistema': [
                'windows', 'linux', 'mac', 'inicio', 'arranque', 'boot',
                'actualizacion', 'parche', 'controlador', 'driver', 'os'
            ],
            'periferico': [
                'impresora', 'escaner', 'proyector', 'camara', 'microfono',
                'altavoz', 'auriculares', 'usb', 'disco externo', 'parlante'
            ]
        }

        self.palabras_prioridad = {
            'critica': [
                'no enciende', 'apaga', 'caida', 'servidor caido', 'emergencia',
                'no funciona', 'todos', 'general', 'panico', 'urgente',
                'inmediato', 'grave', 'critico', 'paralizado', 'detenido'
            ],
            'alta': [
                'error', 'falla', 'rapido', 'importante', 'afecta',
                'bloqueado', 'no puedo', 'no responde'
            ],
            'media': [
                'problema', 'dificultad', 'ayuda', 'necesito', 'lento'
            ],
            'baja': [
                'consulta', 'pregunta', 'informacion', 'como', 'cuando',
                'sugerencia', 'mejora'
            ]
        }

    def _normalizar(self, texto):
        """Convierte a minúsculas y quita acentos"""
        texto = texto.lower()
        reemplazos = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'ñ': 'n', 'ü': 'u'
        }
        for original, reemplazo in reemplazos.items():
            texto = texto.replace(original, reemplazo)
        return texto

    def clasificar_ticket(self, titulo, descripcion):
        """Clasifica un ticket y devuelve categoría, prioridad y confianza"""
        texto = self._normalizar(f"{titulo} {descripcion}")

        # ===== CATEGORÍA =====
        puntajes_categoria = {}
        palabras_detectadas = []

        for categoria, palabras in self.palabras_clave.items():
            coincidencias = [p for p in palabras if p in texto]
            if coincidencias:
                puntajes_categoria[categoria] = len(coincidencias)
                palabras_detectadas.extend(coincidencias)

        if puntajes_categoria:
            categoria = max(puntajes_categoria, key=puntajes_categoria.get)
            total = sum(puntajes_categoria.values())
            confianza_cat = puntajes_categoria[categoria] / total
        else:
            categoria = 'otro'
            confianza_cat = 0.0

        # ===== PRIORIDAD =====
        puntajes_prioridad = {'critica': 0, 'alta': 0, 'media': 0, 'baja': 0}

        for nivel, palabras in self.palabras_prioridad.items():
            for palabra in palabras:
                if palabra in texto:
                    puntajes_prioridad[nivel] += 1

        if any(puntajes_prioridad.values()):
            prioridad = max(puntajes_prioridad, key=puntajes_prioridad.get)
            total_prio = sum(puntajes_prioridad.values())
            confianza_prio = puntajes_prioridad[prioridad] / max(total_prio, 1)
        else:
            prioridad = 'media'
            confianza_prio = 0.3

        # ===== CONFIANZA FINAL =====
        confianza_final = (confianza_cat * 0.6) + (confianza_prio * 0.4)
        confianza_final = round(min(1.0, max(0.1, confianza_final)), 2)

        return {
            'categoria': categoria,
            'prioridad': prioridad,
            'confianza': confianza_final,
            'palabras_detectadas': list(set(palabras_detectadas))[:10]
        }


# Instancia global
motor_triaje = MotorTriaje()


def procesar_ticket_con_ia(titulo, descripcion):
    """Función wrapper para procesar ticket"""
    return motor_triaje.clasificar_ticket(titulo, descripcion)
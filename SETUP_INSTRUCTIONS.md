"""
INSTRUCCIONES DE DESCARGA Y CONFIGURACIÓN
Monitor de Temperatura y Humedad Relativa
==========================================

Este archivo contiene las instrucciones para descargar y ejecutar
el software Monitor de Temperatura y Humedad.

ARCHIVOS A DESCARGAR
====================

Desde el repositorio: https://github.com/juandospino/T-H-Software

Descarga los siguientes archivos Python:
1. ProgramaTH.py         - Aplicación principal
2. base0.py             - Barra de título institucional
3. base1.py             - Pestaña de Reporte
4. base2.py             - Lectura de puerto serial
5. base3.py             - Mapas de calor (Temperatura y Humedad)
6. header_widget.py     - Widget de encabezado personalizado

ESTRUCTURA DE CARPETAS RECOMENDADA
===================================

Monitor/
├── ProgramaTH.py
├── base0.py
├── base1.py
├── base2.py
├── base3.py
├── header_widget.py
├── Logos/
│   ├── icon.ico
│   ├── LogoSemillero.png
│   ├── LogoFisica.png
│   └── UA.png
└── fonts/
    └── Roboto.ttf (opcional)

DEPENDENCIAS REQUERIDAS
=======================

Instala las siguientes librerías ejecutando en la terminal:

pip install PyQt6
pip install pyqtgraph
pip install pandas
pip install numpy
pip install scipy
pip install matplotlib
pip install seaborn
pip install pyserial

O instala todas a la vez:

pip install PyQt6 pyqtgraph pandas numpy scipy matplotlib seaborn pyserial

INSTALACIÓN COMPLETA (Recomendado)
===================================

1. Clonar o descargar el repositorio:
   git clone https://github.com/juandospino/T-H-Software.git
   cd T-H-Software

2. Crear un entorno virtual (opcional pero recomendado):
   python -m venv venv
   
   En Windows:
   venv\Scripts\activate
   
   En macOS/Linux:
   source venv/bin/activate

3. Instalar dependencias:
   pip install -r requirements.txt
   
   Si no existe requirements.txt, instala manualmente:
   pip install PyQt6 pyqtgraph pandas numpy scipy matplotlib seaborn pyserial

4. Ejecutar la aplicación:
   python ProgramaTH.py

CARACTERÍSTICAS PRINCIPALES
============================

✓ Monitor en tiempo real de Temperatura y Humedad
✓ Hasta 6 sensores simultáneos
✓ Mapas de calor interactivos (RdBu_r para temperatura, YlGnBu para humedad)
✓ Gráficas en vivo con pyqtgraph
✓ Reporte estadístico detallado
✓ Exportación de datos (CSV, TXT)
✓ Tema claro/oscuro
✓ Pantalla completa mejorada con controles
✓ Encabezado personalizable con iconos editables
✓ Tres unidades de temperatura: Celsius, Fahrenheit, Kelvin

INSTRUCCIONES DE USO
====================

1. CONEXIÓN SERIAL
   - Conecta los sensores por puerto COM (Windows) o USB (Linux/Mac)
   - Selecciona el puerto y velocidad en baudios (típicamente 9600)
   - Haz clic en "Comenzar" para iniciar el monitoreo

2. MONITOREO
   - Las gráficas se actualizan automáticamente cada 500 ms
   - El mapa de calor se actualiza cada 2 segundos
   - Puedes pausar/reanudar el monitoreo sin perder datos

3. MAPAS DE CALOR
   - Arrastra los marcadores de sensores para ajustar posiciones
   - O edita las coordenadas directamente en los spinboxes
   - El rango de humedad y temperatura se adapta automáticamente
   - Puntos críticos (hotspot/coldspot) se muestran en tiempo real

4. PANTALLA COMPLETA
   - Haz clic en "⛶ Pantalla completa" para expandir los gráficos
   - Usa los controles para:
     * Mostrar/ocultar leyenda
     * Restaurar zoom
     * Guardar gráficos como imagen

5. REPORTE
   - Pestaña "Reporte": estadísticas detalladas por sensor
   - Análisis global: sensores más calientes/fríos
   - Exportar a .txt o guardar backup CSV

MAPAS DE CALOR
==============

TEMPERATURA (RdBu_r):
  🔵 Azul Intenso    → Temperaturas bajas (frío)
  ⚪ Blanco/Gris    → Temperaturas medias
  🔴 Rojo Intenso   → Temperaturas altas (caliente)

HUMEDAD (YlGnBu):
  🟡 Amarillo Claro  → Humedad baja (seco)
  🟢 Verde          → Humedad media
  🔵 Azul Oscuro    → Humedad alta (húmedo)

PERSONALIZACIÓN
===============

Cambiar el icono del programa:
  - Haz clic en el icono en el encabezado para seleccionar otro archivo
  - Formatos soportados: PNG, JPG, JPEG, ICO

Editar título del programa:
  - Modifica la línea en ProgramaTH.py:
    self._header_widget = HeaderWidget(
        title_text="🌡️ Tu Título Aquí 💧",
        ...
    )

Cambiar logos:
  - Reemplaza los archivos en la carpeta Logos/
  - O modifica las rutas en el código

SOLUCIÓN DE PROBLEMAS
=====================

Error: "No module named 'PyQt6'"
  → Instala: pip install PyQt6

Error: "No module named 'pyqtgraph'"
  → Instala: pip install pyqtgraph

Error de puerto serial
  → Verifica la conexión USB
  → Comprueba el puerto en Administrador de dispositivos
  → En Linux: ls /dev/ttyUSB* o ls /dev/ttyACM*

Los gráficos parpadean
  → Reduce la velocidad de actualización en el código si es necesario

Los mapas de calor no se renderizan
  → Instala scipy: pip install scipy

NOTAS TÉCNICAS
==============

- Protocolo serial esperado: sensor_id, temp_c, humedad, (opcional)
- Velocidad por defecto: 9600 baud (ajustable)
- Resolución de interpolación: 150x150 píxeles
- Máximo de 6 sensores simultáneos (ampliable en código)
- Los datos se guardan en CSV automáticamente

ARCHIVOS GENERADOS
===================

Durante la ejecución se crean:
- sensor_data_YYYYMMDD_HHMMSS.csv → Datos en tiempo real
- reporte_YYYYMMDD_HHMMSS.txt → Reporte exportado
- graficos_YYYYMMDD_HHMMSS.png → Gráficos guardados

CRÉDITOS
========

Desarrollo:
  E. Conde
  Y. Avendaño
  J. D. Ospino
  A. Rodríguez

Semillero de Física Computacional
Universidad Autónoma del Caribe

LICENCIA
========

Este proyecto es de código abierto.
Úsalo, modifícalo y comparte libremente.

CONTACTO
========

Para reportar problemas o sugerencias:
https://github.com/juandospino/T-H-Software/issues

Repositorio:
https://github.com/juandospino/T-H-Software

¡Disfruta monitorando!
"""

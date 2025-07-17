#!/usr/bin/env python3
"""
Sistema de Sincronización Google Sheets → Shopify
Prueba Técnica NNC
"""

import logging
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent))

from config.config import config, validate_config
from app.sheets.sheets_client import create_sheets_client

# Configurar logging
logging.basicConfig(
    level=getattr(logging, config.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_google_sheets_connection():
    """Prueba la conexión con Google Sheets"""
    logger.info("🧪 Probando conexión con Google Sheets...")

    try:
        # Crear cliente
        client = create_sheets_client()

        # Obtener metadatos
        metadata = client.get_sheet_metadata()
        logger.info(f"📊 Sheet: {metadata.get('title', 'Sin título')}")
        logger.info(f"📋 Worksheet: {metadata.get('worksheet_title', 'Sin título')}")
        logger.info(f"📏 Filas: {metadata.get('row_count', 0)}")
        logger.info(f"📏 Columnas: {metadata.get('col_count', 0)}")

        # Obtener productos
        products = client.get_all_products()
        logger.info(f"📦 Productos encontrados: {len(products)}")

        if products:
            logger.info("🔍 Primer producto:")
            first_product = products[0]
            for key, value in list(first_product.items())[:5]:
                logger.info(f"  {key}: {value}")

        logger.info("✅ Conexión con Google Sheets exitosa")
        return True

    except Exception as e:
        logger.error(f"❌ Error en conexión con Google Sheets: {e}")
        return False


def main():
    """Función principal"""
    logger.info("🚀 Iniciando Sistema de Sincronización NNC")

    try:
        # Validar configuración
        validate_config()

        # Probar conexión con Google Sheets
        if test_google_sheets_connection():
            logger.info("🎉 Todas las pruebas pasaron exitosamente")
        else:
            logger.error("❌ Falló la prueba de conexión")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
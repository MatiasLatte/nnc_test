import gspread
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional
from google.oauth2.service_account import Credentials
from config.config import config
import time

logger = logging.getLogger(__name__)


@dataclass
class ProductData:
    """Data structure for each product"""
    part: str
    price: float
    weight: int
    tag: str
    collection: str

    def to_dict(self) -> dict:
        return {
            'part': self.part,
            'price': self.price,
            'weight': self.weight,
            'tag': self.tag,
            'collection': self.collection,
        }

    @classmethod
    def from_row(cls, row_data: Dict) -> 'ProductData':
        """Crea ProductData desde una fila del sheet"""
        return cls(
            part=row_data.get('part_no', ''),
            price=float(row_data.get('price', 0)),
            weight=int(row_data.get('weight', 0)),
            tag=row_data.get('tag', ''),
            collection=row_data.get('collection', '')
        )


class GoogleSheetsClient:
    """Cliente para interactuar con Google Sheets"""

    def __init__(self):
        self.client = None
        self.workbook = None
        self.sheet = None
        self.connect()

    def connect(self):
        """Conecta con Google Sheets usando credenciales de service account"""
        try:
            # Ruta a las credenciales
            credentials_path = Path(__file__).resolve().parents[2] / config.google_sheets.credentials_path

            # Scope necesario para Google Sheets
            scope = ["https://www.googleapis.com/auth/spreadsheets"]

            # Autenticación con service account
            creds = Credentials.from_service_account_file(str(credentials_path), scopes=scope)
            self.client = gspread.authorize(creds)

            # Abrir el spreadsheet por ID
            self.workbook = self.client.open_by_key(config.google_sheets.sheet_id)

            # Obtener la worksheet "VOIP"
            try:
                self.sheet = self.workbook.worksheet("VOIP")
            except gspread.WorksheetNotFound:
                # Si no existe, usar la primera worksheet
                self.sheet = self.workbook.sheet1
                logger.warning("Worksheet 'VOIP' no encontrada, usando la primera worksheet")

            logger.info(f"✅ Conectado exitosamente a Google Sheets: {self.workbook.title}")
            logger.info(f"📊 Worksheet activa: {self.sheet.title}")

        except Exception as e:
            logger.error(f"❌ Error conectando a Google Sheets: {e}")
            raise

    def get_all_products(self) -> List[Dict]:
        """
        Obtiene todos los productos del sheet
        Retorna lista de diccionarios con los datos normalizados
        """
        try:
            # Obtener todos los registros
            records = self.sheet.get_all_records()

            if not records:
                logger.warning("No se encontraron productos en el sheet")
                return []

            # Limpiar y normalizar datos
            products = []
            for i, record in enumerate(records, start=2):  # Start=2 porque row 1 son headers
                try:
                    # Saltar filas completamente vacías
                    if not record or not any(str(value).strip() for value in record.values()):
                        continue

                    # Normalizar nombres de columnas y valores
                    normalized_record = {}
                    for key, value in record.items():
                        # Limpiar key
                        clean_key = str(key).lower().strip().replace(' ', '_').replace('-', '_')

                        # Limpiar value
                        clean_value = str(value).strip() if value else ""

                        normalized_record[clean_key] = clean_value

                    # Validar que tenga campos esenciales
                    if not self._validate_product_record(normalized_record, i):
                        continue

                    # Agregar metadatos
                    normalized_record['_row_number'] = i
                    normalized_record['_sheet_name'] = self.sheet.title

                    products.append(normalized_record)

                except Exception as e:
                    logger.error(f"Error procesando fila {i}: {e}")
                    continue

            logger.info(f"📦 Obtenidos {len(products)} productos válidos del sheet")
            return products

        except Exception as e:
            logger.error(f"❌ Error obteniendo productos: {e}")
            return []

    def _validate_product_record(self, record: Dict, row_number: int) -> bool:
        """Valida que un registro tenga los campos mínimos requeridos"""
        required_fields = ['part_no']  # Según especificaciones, Part No es el campo clave

        for field in required_fields:
            if not record.get(field):
                logger.warning(f"Fila {row_number}: Falta campo requerido '{field}'")
                return False

        return True

    def get_product_by_part_no(self, part_no: str) -> Optional[Dict]:
        """Obtiene un producto específico por Part No"""
        try:
            products = self.get_all_products()

            for product in products:
                if product.get('part_no') == part_no:
                    return product

            return None

        except Exception as e:
            logger.error(f"Error obteniendo producto {part_no}: {e}")
            return None

    def get_sheet_metadata(self) -> Dict:
        """Obtiene metadatos del sheet para tracking de cambios"""
        try:
            # Información básica del sheet
            sheet_info = {
                'title': self.workbook.title,
                'worksheet_title': self.sheet.title,
                'url': self.workbook.url,
                'row_count': self.sheet.row_count,
                'col_count': self.sheet.col_count,
                'last_updated': getattr(self.workbook, 'lastUpdateTime', None)
            }

            # Headers del sheet
            try:
                headers = self.sheet.row_values(1)
                sheet_info['headers'] = headers
                sheet_info['header_count'] = len(headers)
            except Exception as e:
                logger.error(f"Error obteniendo headers: {e}")
                sheet_info['headers'] = []

            return sheet_info

        except Exception as e:
            logger.error(f"Error obteniendo metadatos: {e}")
            return {}

    def watch_for_changes(self, callback_function, interval: int = None):
        """
        Monitorea cambios en el sheet mediante polling
        """
        if interval is None:
            interval = config.sync_interval

        logger.info(f"🔄 Iniciando monitoreo de cambios (intervalo: {interval}s)")

        last_data_hash = None

        while True:
            try:
                # Obtener datos actuales
                current_data = self.get_all_products()

                # Calcular hash simple para detectar cambios
                current_hash = hash(str(sorted(current_data, key=lambda x: x.get('part_no', ''))))

                # Si hay cambios, ejecutar callback
                if last_data_hash is None:
                    logger.info("🔄 Primera carga de datos")
                    callback_function(current_data)
                elif current_hash != last_data_hash:
                    logger.info("🔄 Cambios detectados en el sheet")
                    callback_function(current_data)
                else:
                    logger.debug("✅ No hay cambios en el sheet")

                last_data_hash = current_hash

                # Esperar antes del próximo check
                time.sleep(interval)

            except Exception as e:
                logger.error(f"❌ Error en monitoreo: {e}")
                time.sleep(interval * 2)  # Esperar más tiempo si hay error

    def refresh_connection(self):
        """Refresca la conexión con Google Sheets"""
        try:
            logger.info("🔄 Refrescando conexión con Google Sheets...")
            self.connect()
        except Exception as e:
            logger.error(f"❌ Error refrescando conexión: {e}")
            raise

    def get_connection_status(self) -> bool:
        """Verifica el estado de la conexión"""
        try:
            # Intentar obtener información básica del sheet
            title = self.workbook.title
            return True
        except Exception as e:
            logger.error(f"❌ Conexión perdida: {e}")
            return False


# Función helper para crear cliente
def create_sheets_client() -> GoogleSheetsClient:
    """Factory function para crear cliente de Google Sheets"""
    return GoogleSheetsClient()


# Ejemplo de uso
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO)

    try:
        # Crear cliente
        client = create_sheets_client()

        # Obtener metadatos
        metadata = client.get_sheet_metadata()
        print("📊 Metadatos del sheet:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")

        # Obtener productos
        products = client.get_all_products()
        print(f"\n📦 Productos encontrados: {len(products)}")

        if products:
            print("\n🔍 Primer producto:")
            for key, value in list(products[0].items())[:5]:  # Mostrar solo primeros 5 campos
                print(f"  {key}: {value}")

    except Exception as e:
        logger.error(f"❌ Error en ejemplo: {e}")
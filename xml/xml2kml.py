import xml.etree.ElementTree as ET

class Kml(object):
    """
    Genera archivo KML con puntos y líneas
    @version 1.1 19/Octumbre/2024
    @author: Juan Manuel Cueva Lovelle. Universidad de Oviedo
    """
    def __init__(self):
        """
        Crea el elemento raíz y el espacio de nombres
        """
        self.raiz = ET.Element('kml', xmlns="http://www.opengis.net/kml/2.2")
        self.doc = ET.SubElement(self.raiz,'Document')

    def addPlacemark(self,nombre,descripcion,long,lat,alt, modoAltitud,color = None):
        """
        Añade un elemento <Placemark> con puntos <Point>
        """
        pm = ET.SubElement(self.doc,'Placemark')
        ET.SubElement(pm,'name').text = nombre
        ET.SubElement(pm,'description').text = descripcion
        
        estilo = ET.SubElement(pm, "Style")
        icon_style = ET.SubElement(estilo, "IconStyle")
        if color:
            ET.SubElement(icon_style, "color").text = color
        ET.SubElement(icon_style, "scale").text = "0.8"

        icono = ET.SubElement(icon_style, "Icon")
        # Icono de círculo limpio en lugar de chincheta
        ET.SubElement(
            icono, "href"
        ).text = (
            "http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png"
        )
        punto = ET.SubElement(pm,'Point')
        ET.SubElement(punto,'coordinates').text = '{},{},{}'.format(long,lat,alt)
        ET.SubElement(punto,'altitudeMode').text = modoAltitud

    def addLineString(self,nombre,extrude,tesela, listaCoordenadas, modoAltitud, color, ancho):
        """
        Añade un elemento <Placemark> con líneas <LineString>
        """
        ET.SubElement(self.doc,'name').text = nombre
        pm = ET.SubElement(self.doc,'Placemark')
        ls = ET.SubElement(pm, 'LineString')
        ET.SubElement(ls,'extrude').text = extrude
        ET.SubElement(ls,'tessellation').text = tesela
        ET.SubElement(ls,'coordinates').text = listaCoordenadas
        ET.SubElement(ls,'altitudeMode').text = modoAltitud 

        estilo = ET.SubElement(pm, 'Style')
        linea = ET.SubElement(estilo, 'LineStyle')
        ET.SubElement (linea, 'color').text = color
        ET.SubElement (linea, 'width').text = ancho

    def escribir(self,nombreArchivoKML):
        """
        Escribe el archivo KML con declaración y codificación
        """
        arbol = ET.ElementTree(self.raiz)
        ET.indent(arbol)
        arbol.write(nombreArchivoKML, encoding='utf-8', xml_declaration=True)
    
    def ver(self):
        """
        Muestra el archivo KML. Se utiliza para depurar
        """
        print("\nElemento raiz = ", self.raiz.tag)

        if self.raiz.text != None:
            print("Contenido = "    , self.raiz.text.strip('\n'))
        else:
            print("Contenido = "    , self.raiz.text)
        
        print("Atributos = "    , self.raiz.attrib)

        for hijo in self.raiz.findall('.//'):
            print("\nElemento = " , hijo.tag)
            if hijo.text != None:
                print("Contenido = ", hijo.text.strip('\n'))
            else:
                print("Contenido = ", hijo.text)    
            print("Atributos = ", hijo.attrib)

class Xml2Kml(object):
    def __init__(self, archivo_xml, archivo_kml):
        self.archivo_xml = archivo_xml
        self.archivo_kml = archivo_kml
        self.kml = Kml()

    def _extraer_coordenadas(self, nodo):
        lon = nodo.find("./ns:longitud", self.ns).text.strip()
        lat = nodo.find("./ns:latitud", self.ns).text.strip()
        alt = nodo.find("./ns:altitud", self.ns).text.strip()
        return lon, lat, alt

    def convertir(self):
        arbol_xml = ET.parse(self.archivo_xml)
        raiz = arbol_xml.getroot()

        # Detección dinámica del namespace
        if raiz.tag.startswith("{"):
            uri_namespace = raiz.tag.split("}")[0].strip("{")
            self.ns = {"ns": uri_namespace}
        else:
            self.ns = {"ns": ""}

        modo_altitud = "clampedToGround"

        COLOR_ROJO = "ff0000ff"    # Rojo para Salida y Meta
        COLOR_AZUL = "ffff0000"    # Azul para Sprint Intermedio
        COLOR_AMARILLO = "ff00ffff" # Amarillo para puntos anónimos con nombre

        salida_nodo = raiz.find(".//ns:lugar-salida", self.ns)
        meta_nodo = raiz.find(".//ns:lugar-meta", self.ns)
        sprint_nodo = raiz.find(".//ns:sprint-intermedio", self.ns)

        lista_coordenadas = []

        # 1. Procesar Salida (Rojo)
        if salida_nom_nodo := salida_nodo.find(".//ns:nombre", self.ns) if salida_nodo is not None else None:
            nombre_salida = salida_nom_nodo.text.strip()
        else:
            nombre_salida = "Salida"
            
        if salida_nodo is not None:
            lon, lat, alt = self._extraer_coordenadas(salida_nodo)
            self.kml.addPlacemark(
                nombre_salida,
                "Lugar de Salida de la Etapa",
                lon,
                lat,
                alt,
                modo_altitud,
                color=COLOR_ROJO,
            )
            lista_coordenadas.append(f"{lon},{lat},{alt}")

        # 2. Puntos Anónimos (Amarillos si tienen nombre, o sin nombre)
        puntos_anonimos = raiz.findall(".//ns:puntos-anon/ns:punto-anon", self.ns)

        for punto in puntos_anonimos:
            lon, lat, alt = self._extraer_coordenadas(punto)
            lista_coordenadas.append(f"{lon},{lat},{alt}")

            nom_elem = punto.find("ns:nombre", self.ns) or punto.find("ns:nombre-punto", self.ns)
            nombre_punto = nom_elem.text.strip() if nom_elem is not None else ""

            # Si tiene nombre, lo marcamos en amarillo como se pidió
            if nombre_punto:
                self.kml.addPlacemark(
                    nombre_punto,
                    f"Punto de paso: {nombre_punto}",
                    lon,
                    lat,
                    alt,
                    modo_altitud,
                    color=COLOR_AMARILLO,
                )

        # 3. Sprint Intermedio (Azul)
        if sprint_nodo is not None:
            lon, lat, alt = self._extraer_coordenadas(sprint_nodo)
            nom_elem = sprint_nodo.find("ns:nombre", self.ns) or sprint_nodo.find("ns:nombre-punto", self.ns)
            nombre_sprint = nom_elem.text.strip() if nom_elem is not None else "Sprint Intermedio"
            
            self.kml.addPlacemark(
                nombre_sprint,
                "Sprint Intermedio",
                lon,
                lat,
                alt,
                modo_altitud,
                color=COLOR_AZUL,
            )

        # 4. Meta (Rojo)
        if meta_nodo is not None:
            lon, lat, alt = self._extraer_coordenadas(meta_nodo)
            nom_elem = meta_nodo.find("ns:nombre", self.ns) or meta_nodo.find("ns:nombre-punto", self.ns)
            nombre_meta = nom_elem.text.strip() if nom_elem is not None else "Meta"

            self.kml.addPlacemark(
                nombre_meta,
                "Lugar de Meta de la Etapa",
                lon,
                lat,
                alt,
                modo_altitud,
                color=COLOR_ROJO,
            )
            lista_coordenadas.append(f"{lon},{lat},{alt}")

        # 5. Creación de la línea del recorrido
        string_coordenadas = "\n".join(lista_coordenadas)
        self.kml.addLineString(
            "Recorrido de la Etapa",
            extrude="1",
            tesela="1",
            listaCoordenadas=string_coordenadas,
            modoAltitud=modo_altitud,
            color=COLOR_ROJO,
            ancho="4",
        )
        self.kml.escribir(self.archivo_kml)
        print(f"Archivo KML generado correctamente en: {self.archivo_kml}")


if __name__ == "__main__":
    convertidor = Xml2Kml("etapaEsquema.xml", "etapa.kml")
    convertidor.convertir()

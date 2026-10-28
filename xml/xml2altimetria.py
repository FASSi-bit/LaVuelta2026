import xml.etree.ElementTree as ET


class Svg(object):

    def __init__(self):
        self.raiz = ET.Element(
            "svg", xmlns="http://www.w3.org/2000/svg", version="2.0"
        )

    def addRect(self, x, y, width, height, fill, strokeWidth, stroke):
        ET.SubElement(
            self.raiz,
            "rect",
            x=str(x),
            y=str(y),
            width=str(width),
            height=str(height),
            fill=fill,
            strokeWidth=str(strokeWidth),
            stroke=stroke,
        )

    def addCircle(self, cx, cy, r, fill):
        ET.SubElement(
            self.raiz,
            "circle",
            cx=str(cx),
            cy=str(cy),
            r=str(r),
            fill=fill,
        )

    def addLine(self, x1, y1, x2, y2, stroke, strokeWith):
        ET.SubElement(
            self.raiz,
            "line",
            x1=str(x1),
            y1=str(y1),
            x2=str(x2),
            y2=str(y2),
            stroke=stroke,
            strokeWith=str(strokeWith),
        )

    def addPolyline(self, points, stroke, strokeWith, fill):
        ET.SubElement(
            self.raiz,
            "polyline",
            points=points,
            stroke=stroke,
            strokeWith=str(strokeWith),
            fill=fill,
        )

    def addText(self, texto, x, y, fontFamily, fontSize, style, transform=None):
        attribs = {
            "x": str(x),
            "y": str(y),
            "font-family": fontFamily,
            "font-size": str(fontSize),
            "style": style,
        }
        if transform:
            attribs["transform"] = transform

        elem = ET.SubElement(self.raiz, "text", **attribs)
        elem.text = texto

    def escribir(self, nombreArchivoSVG):
        arbol = ET.ElementTree(self.raiz)
        ET.indent(arbol)
        arbol.write(nombreArchivoSVG, encoding="utf-8", xml_declaration=True)

    def ver(self):
        print("\nElemento raiz = ", self.raiz.tag)

        if self.raiz.text != None:
            print("Contenido = ", self.raiz.text.strip("\n"))
        else:
            print("Contenido = ", self.raiz.text)

        print("Atributos = ", self.raiz.attrib)

        for hijo in self.raiz.findall(".//"):
            print("\nElemento = ", hijo.tag)
            if hijo.text != None:
                print("Contenido = ", hijo.text.strip("\n"))
            else:
                print("Contenido = ", hijo.text)
            print("Atributos = ", hijo.attrib)


class Xml2Altimetria(object):

    def __init__(self, archivo_xml, archivo_svg):
        self.archivo_xml = archivo_xml
        self.archivo_svg = archivo_svg
        self.svg = Svg()
        self.ns = ""

        self.ancho_svg = 1200
        self.alto_svg = 700
        self.margen_x = 90
        self.margen_y = 150

    def _obtener_datos_puntos(self, root):
        puntos_datos = []

        # Extraer namespace
        if root.tag.startswith("{"):
            self.ns = root.tag.split("}")[0] + "}"

        # 1. Salida
        salida_elem = root.find(f".//{self.ns}lugar-salida")
        if salida_elem is not None:
            nom_elem = salida_elem.find(f"{self.ns}nombre") or salida_elem.find(f"{self.ns}nombre-punto")
            alt_elem = salida_elem.find(f"{self.ns}altitud")
            puntos_datos.append({
                "nombre": (
                    nom_elem.text.strip()
                    if nom_elem is not None
                    else "Salida"
                ),
                "distancia": 0.0,
                "altitud": (
                    float(alt_elem.text.strip()) if alt_elem is not None else 0.0
                ),
                "es_hito": True,
            })

        # 2. Puntos Anónimos (se ignoran los que están en distancia 0.0 para evitar duplicar con la salida)
        for p in root.findall(f".//{self.ns}punto-anon"):
            dist_elem = p.find(f"{self.ns}distancia-salida")
            alt_elem = p.find(f"{self.ns}altitud")
            nom_elem = p.find(f"{self.ns}nombre") or p.find(f"{self.ns}nombre-punto")
            
            distancia = float(dist_elem.text.strip()) if dist_elem is not None else 0.0
            if distancia == 0.0:
                continue

            nombre_p = nom_elem.text.strip() if nom_elem is not None else ""

            if dist_elem is not None and alt_elem is not None:
                puntos_datos.append({
                    "nombre": nombre_p,
                    "distancia": distancia,
                    "altitud": float(alt_elem.text.strip()),
                    "es_hito": bool(nombre_p),
                })

        # 3. Sprints Intermedios
        for sprint in root.findall(f".//{self.ns}sprint-intermedio"):
            dist_elem = sprint.find(f"{self.ns}distancia-salida")
            alt_elem = sprint.find(f"{self.ns}altitud")
            nom_elem = sprint.find(f"{self.ns}nombre") or sprint.find(f"{self.ns}nombre-punto")
            if dist_elem is not None and alt_elem is not None:
                puntos_datos.append({
                    "nombre": (
                        nom_elem.text.strip()
                        if nom_elem is not None
                        else "Sprint Intermedio"
                    ),
                    "distancia": float(dist_elem.text.strip()),
                    "altitud": float(alt_elem.text.strip()),
                    "es_hito": True,
                })

        # 4. Meta
        meta_elem = root.find(f".//{self.ns}lugar-meta")
        longitud_elem = root.find(f".//{self.ns}longitud-etapa")
        dist_meta = (
            float(longitud_elem.text.strip())
            if longitud_elem is not None
            else 112.0
        )

        if meta_elem is not None:
            nom_elem = meta_elem.find(f"{self.ns}nombre") or meta_elem.find(f"{self.ns}nombre-punto")
            alt_elem = meta_elem.find(f"{self.ns}altitud")
            puntos_datos.append({
                "nombre": (
                    nom_elem.text.strip() if nom_elem is not None else "Meta"
                ),
                "distancia": dist_meta,
                "altitud": (
                    float(alt_elem.text.strip()) if alt_elem is not None else 0.0
                ),
                "es_hito": True,
            })

        # Ordenar por kilometraje
        puntos_datos.sort(key=lambda x: x["distancia"])
        return puntos_datos

    def convertir(self):
        arbol_xml = ET.parse(self.archivo_xml)
        raiz = arbol_xml.getroot()

        puntos = self._obtener_datos_puntos(raiz)

        if not puntos:
            print("No se encontraron puntos en el XML.")
            return

        nombre_etapa_elem = raiz.find(f".//{self.ns}nombre")
        nombre_etapa = (
            nombre_etapa_elem.text.strip()
            if nombre_etapa_elem is not None
            else "Perfil de Altimetría"
        )

        dist_min = min(p["distancia"] for p in puntos)
        dist_max = max(p["distancia"] for p in puntos)

        # Eje Y fijado exactamente entre 0m y 900m
        alt_min = 0.0
        alt_max = 900.0

        ancho_util = self.ancho_svg - 2 * self.margen_x
        alto_util = self.alto_svg - 2 * self.margen_y

        def transform_x(d):
            if dist_max == dist_min:
                return self.margen_x
            return self.margen_x + (d - dist_min) / (
                dist_max - dist_min
            ) * ancho_util

        def transform_y(a):
            return (
                self.alto_svg
                - self.margen_y
                - (a - alt_min) / (alt_max - alt_min) * alto_util
            )

        # Fondo del contenedor
        self.svg.addRect(
            0,
            0,
            self.ancho_svg,
            self.alto_svg,
            fill="#ffffff",
            strokeWidth=0,
            stroke="none",
        )

        # Título
        self.svg.addText(
            f"Altimetría: {nombre_etapa}",
            x=self.margen_x,
            y=40,
            fontFamily="sans-serif",
            fontSize=18,
            style="font-weight: bold; fill: #1e293b;",
        )

        y_suelo = self.alto_svg - self.margen_y

        # Marcas y cuadrícula del Eje Y (0, 300, 600, 900 metros)
        marcas_y = [0, 300, 600, 900]
        for val_alt in marcas_y:
            py = transform_y(val_alt)
            self.svg.addLine(
                self.margen_x,
                py,
                self.ancho_svg - self.margen_x,
                py,
                stroke="#e2e8f0",
                strokeWith=1,
            )
            self.svg.addText(
                f"{int(val_alt)} m",
                x=self.margen_x - 55,
                y=py + 4,
                fontFamily="sans-serif",
                fontSize=11,
                style="fill: #475569; font-weight: bold;",
            )

        # Ejes base
        self.svg.addLine(
            self.margen_x,
            y_suelo,
            self.ancho_svg - self.margen_x,
            y_suelo,
            stroke="#000000",
            strokeWith=2,
        )
        self.svg.addLine(
            self.margen_x,
            self.margen_y,
            self.margen_x,
            y_suelo,
            stroke="#000000",
            strokeWith=2,
        )

        # Construcción de la superficie (Polígono)
        pts_perfil = []
        for p in puntos:
            px = transform_x(p["distancia"])
            py = transform_y(p["altitud"])
            pts_perfil.append(f"{px:.2f},{py:.2f}")

        x_inicio = transform_x(puntos[0]["distancia"])
        x_fin = transform_x(puntos[-1]["distancia"])
        pts_sombra = (
            [f"{x_inicio:.2f},{y_suelo}"]
            + pts_perfil
            + [f"{x_fin:.2f},{y_suelo}"]
        )

        self.svg.addPolyline(
            points=" ".join(pts_sombra),
            stroke="none",
            strokeWith=0,
            fill="#e0f2fe",
        )
        self.svg.addPolyline(
            points=" ".join(pts_perfil),
            stroke="#0284c7",
            strokeWith=3,
            fill="none",
        )

        # Renderizado de puntos nombrados / hitos en el Eje X y en el perfil
        for p in puntos:
            px = transform_x(p["distancia"])
            py = transform_y(p["altitud"])

            # Si el punto tiene un nombre definido, se dibuja su etiqueta en el eje X
            if p["nombre"]:
                # Línea indicadora vertical
                self.svg.addLine(
                    px,
                    py,
                    px,
                    y_suelo,
                    stroke="#dc2626" if p["es_hito"] else "#94a3b8",
                    strokeWith=1,
                )

                # Círculo en la gráfica
                self.svg.addCircle(
                    cx=px,
                    cy=py,
                    r=4 if p["es_hito"] else 3,
                    fill="#dc2626" if p["es_hito"] else "#0284c7",
                )

                # Marca pequeña en el eje X
                self.svg.addLine(
                    px,
                    y_suelo,
                    px,
                    y_suelo + 6,
                    stroke="#000000",
                    strokeWith=1,
                )

                # Texto rotado en el eje X para evitar solapamientos
                texto_eje_x = f"{p['nombre']} ({p['distancia']:.1f} km)"
                self.svg.addText(
                    texto_eje_x,
                    x=px - 5,
                    y=y_suelo + 20,
                    fontFamily="sans-serif",
                    fontSize=10,
                    style="fill: #0f172a; font-weight: bold;" if p["es_hito"] else "fill: #475569;",
                    transform=f"rotate(45, {px}, {y_suelo + 20})"
                )

        self.svg.escribir(self.archivo_svg)
        print(f"SVG generado correctamente en: {self.archivo_svg}")


if __name__ == "__main__":
    convertidor = Xml2Altimetria("etapaEsquema.xml", "altimetria.svg")
    convertidor.convertir()
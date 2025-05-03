from lxml import etree
import time
import output_parquet as op


def extract_xml_values(nodo, prefijo, source_dict):
    source_dict.update(
        {prefijo + key: value for key, value in nodo.items() if "{" not in key}
    )

def parse_concepto(UUID, ns, source, conceptos_list):
    conceptos = source.find(ns + "Conceptos")
    if conceptos is not None:
        concepto = conceptos.findall(ns + "Concepto")

        # Iterar dentro de Conceptos y guardar los valores
        for id, item in enumerate(concepto):
            conceptos_data = {}
            conceptos_data["UUID"] = UUID
            conceptos_data["ID"] = id
            extract_xml_values(item, "", conceptos_data)

            for referencia in (
                "InformacionAduanera",
                "ACuentaTerceros",
                "CuentaPredial",
            ):
                node2 = item.find(ns + referencia)
                if node2 is not None:
                    extract_xml_values(node2, referencia + "_", conceptos_data)
            conceptos_list.append(conceptos_data.copy())

def parse_impuestos(UUID, ns, source, traslados_list, retenciones_list):
    conceptos = source.find(ns + "Conceptos")
    if conceptos is not None:
        concepto = conceptos.findall(ns + "Concepto")
        for id, item in enumerate(concepto):
            impuestos = item.find(ns + "Impuestos")
            if impuestos is not None:
                traslados = impuestos.find(ns + "Traslados")
                if traslados is not None:
                    traslado = traslados.findall(ns + "Traslado")
                    for id2, item2 in enumerate(traslado):
                        traslados_data = {}
                        traslados_data["UUID"] = UUID
                        traslados_data["ID"] = id
                        traslados_data["ID2"] = id2
                        extract_xml_values(item2, "", traslados_data)
                        traslados_list.append(traslados_data.copy())

                retenciones = impuestos.find(ns + "Retenciones")
                if retenciones is not None:
                    retencion = retenciones.findall(ns + "Retencion")
                    for id2, item2 in enumerate(retencion):
                        retenciones_data = {}
                        retenciones_data["UUID"] = UUID
                        retenciones_data["ID"] = id
                        retenciones_data["ID2"] = id2
                        extract_xml_values(item2, "", retenciones_data)
                        retenciones_list.append(retenciones_data.copy())

def parse_nomina(UUID, ns, source, nominas_list):
    nomina_data = {}
    nominas = source.find(ns + "Nomina")
    extract_xml_values(nominas, "Nomina_", nomina_data)
    nomina_data["UUID"] = UUID
    nominas_list.append(nomina_data.copy())
    """ 
    if nominas != None:
        concepto = nominas.findall(ns + "Concepto")

        #Iterar dentro de Conceptos y guardar los valores
        for id, item in enumerate(concepto):
            conceptos_data = {}               
            conceptos_data["UUID"] = UUID
            conceptos_data["ID"] = id                
            extract_xml_values(item, "",conceptos_data)

            for referencia in ["InformacionAduanera","ACuentaTerceros","CuentaPredial"]:
                node2 = item.find(ns + referencia)
                if node2 != None:
                    extract_xml_values(node2, referencia + "_", conceptos_data)
            
    """

def parse_cfdi(files_tipos_list):
    start_time2 = time.time()
    NS_TFD = "{http://www.sat.gob.mx/TimbreFiscalDigital}"
    NS_NOMINA = "{http://www.sat.gob.mx/nomina12}"
    EXCLUIDOS = (
        "Certificado",
        "NoCertificado",
        "Sello",
        "TFD_NoCertificadoSAT",
        "TFD_SelloCFD",
        "TFD_SelloSAT",
    )
    TFD = "TimbreFiscalDigital"
    OUTPUT_LIMIT = 100000
    tipos = files_tipos_list[0]
    xml_file_list = files_tipos_list[1]

    data_comprobante, data_concepto, data_traslado, data_retencion, data_nomina = (
        [],
        [],
        [],
        [],
        [],
    )

    file_list_lenght = len(xml_file_list)

    count_runs, count_filebreak = 0, 0

    for xml_file in xml_file_list:
        # Mensajes de progreso
        count_runs = count_runs + 1
        count_filebreak = count_filebreak + 1

        # Parse la raiz y sus valores
        comprobante_data = {}
        tree = etree.parse(xml_file)
        root = tree.getroot()
        ns_cfdi = "{" + root.nsmap.get("cfdi") + "}"
        extract_xml_values(root, "", comprobante_data)

        for referencia in ("Emisor", "Receptor", "Impuestos", "InformacionGlobal"):
            node = root.find(ns_cfdi + referencia)
            if node is not None:
                extract_xml_values(node, referencia + "_", comprobante_data)

        # Parse el TFD y sus valores de Complemento o de la Raiz, con o sin namespace
        complemento = root.find(ns_cfdi + "Complemento")
        if complemento is not None:
            tfd = complemento.find(NS_TFD + TFD)
            if tfd is None:
                tfd = complemento.find(TFD)
        else:
            tfd = root.find(NS_TFD + TFD)
            if tfd is None:
                tfd = root.find(TFD)
        extract_xml_values(tfd, "TFD_", comprobante_data)
        UUID = comprobante_data["TFD_UUID"]

        # Eliminar elementos no deseados
        for x in EXCLUIDOS:
            del comprobante_data[x]

        data_comprobante.append(comprobante_data.copy())

        if comprobante_data["TipoDeComprobante"] == "N":
            parse_concepto(UUID, ns_cfdi, root, data_concepto)
            parse_nomina(UUID, NS_NOMINA, complemento, data_nomina)
        else:
            parse_concepto(UUID, ns_cfdi, root, data_concepto)
            parse_impuestos(UUID, ns_cfdi, root, data_traslado, data_retencion)

        if file_list_lenght > OUTPUT_LIMIT:
            if count_filebreak > OUTPUT_LIMIT:
                print(round(count_runs / file_list_lenght * 100, 2), "%, ", count_runs)
                print(round((time.time() - start_time2) / 60, 2), "min")
                count_filebreak = 0
                op.append_to_parquet(
                    data_comprobante, "Output/" + tipos[0] + str(count_runs)
                )
                data_comprobante.clear()
                op.append_to_parquet(
                    data_concepto, "Output/" + tipos[1] + str(count_runs)
                )
                data_concepto.clear()
                op.append_to_parquet(
                    data_traslado, "Output/" + tipos[2] + str(count_runs)
                )
                data_traslado.clear()
                op.append_to_parquet(
                    data_retencion, "Output/" + tipos[3] + str(count_runs)
                )
                data_retencion.clear()
                op.append_to_parquet(
                    data_nomina, "Output/" + tipos[4] + str(count_runs)
                )
                data_nomina.clear()
    xml_file_list.clear()
    op.append_to_parquet(data_comprobante, "Output/" + tipos[0] + str(count_runs))
    data_comprobante.clear()
    op.append_to_parquet(data_concepto, "Output/" + tipos[1] + str(count_runs))
    data_concepto.clear()
    op.append_to_parquet(data_traslado, "Output/" + tipos[2] + str(count_runs))
    data_traslado.clear()
    op.append_to_parquet(data_retencion, "Output/" + tipos[3] + str(count_runs))
    data_retencion.clear()
    op.append_to_parquet(data_nomina, "Output/" + tipos[4] + str(count_runs))
    data_nomina.clear()

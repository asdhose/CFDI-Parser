import multiprocessing
import os
import cfdi_parser as parser
import output_parquet as op
import time


def test_fake_volume(file_list, mult):
    test_list = []
    for x in range(mult):
        for y in file_list:
            test_list.append(y)
    return test_list

def split_parts(num_cores, execution_id, tipos, file_list):
    list_size = len(file_list)
    part_size = list_size // num_cores  # Use integer division for cleaner splits
    remainder = list_size % num_cores  # Handle leftover files

    list_results = []
    part_index = 0

    for part in range(num_cores):
        lista_tipos = [
            f"{execution_id}{part}{tipo}" for tipo in tipos
        ]  # Generate type list

        # Distribute extra files evenly
        extra = 1 if part < remainder else 0
        lista_archivos = file_list[part_index : part_index + part_size + extra]
        part_index += part_size + extra

        tuple_part = (lista_tipos, lista_archivos)  # Correctly define tuple
        list_results.append(tuple_part)  # Append the tuple correctly

    return list_results


if __name__ == "__main__":
    start_time = time.time()

    num_cores = multiprocessing.cpu_count()-1
    #num_cores = 8
    tipos = ("Comprobante", "Conceptos", "Traslados", "Retenciones", "Nominas")

    #FOLDER_PATH = r"C:\Users\Jose\Documents\Development\CFDI Parser\Test_XMLs\Originales"
    #FOLDER_PATH = r"C:\Users\Jose\Documents\CFDI Sample"
    FOLDER_PATH = r"C:\Users\Jose\Documents\CFDI Sample2"

    xml_file_list = [
        os.path.join(FOLDER_PATH, file)
        for file in os.listdir(FOLDER_PATH)
        if file.endswith(".xml")
    ]

    #Parte la lista de archivos entre num_cores para ser ejecutado en paralelo
    #para cada ejecucion crea una tupla donde
    #0: es la lista de archivos, 1: es tipos con un prefijo para el output
    split_list = split_parts(num_cores, 1 , tipos, xml_file_list)

    '''
    #Run in single process
    for x in split_list:
        parser.parse_cfdi(x)
    '''

    
    #Run in parallel super fast and cool
    
    with multiprocessing.Pool(num_cores) as pool:
        pool.map(parser.parse_cfdi, split_list)
    

    for tipo in tipos:
        op.consolidate_files("Output/", tipo)

    print("--- %s seconds ---" % (time.time() - start_time))





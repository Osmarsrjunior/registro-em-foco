# Dicionário dos dados

## territories.csv

| Campo | Tipo e unidade | Definição |
| --- | --- | --- |
| year | Inteiro | Ano de ocorrência de referência da publicação |
| code | Texto | BR, sigla UF, grande região ou IGN |
| name | Texto | Nome territorial preservado da tabela, com Total Brasil normalizado para Brasil |
| level | Categoria | country, region, state ou unknown |
| region | Texto | Grande região, preenchida apenas para UF |
| estimated_births | Número de eventos | Total estimado publicado; pode ter casas decimais |
| rate | Percentual de 0 a 100 | Taxa de sub-registro do IBGE; 0.9548 significa 0,9548% |
| health_underreporting | Percentual ou vazio | Subnotificação da base do Ministério da Saúde; indicador distinto |
| estimated_missing | Número aproximado de eventos | estimated_births × rate / 100, arredondado a seis casas |
| source_table | Texto | Número da tabela de origem |

Os agregados regionais e nacional já constam das fontes e não devem ser somados às UFs. A categoria IGN é preservada. As taxas nacionais não são médias simples estaduais. DF é a denominação presente na tabela utilizada.

## municipalities_2024.csv

Contém year, uf, code (código municipal de sete dígitos como texto), name, estimated_births, rate, estimated_missing e source_table. A base complementar cobre 5.570 registros. Nantes (3532157), Peritiba (4212601) e Anhanguera (5201207) têm medidas vazias na extração, preservando o marcador “.” da fonte como ausência. Não imputamos zero, não interpolamos e não inferimos a causa da ausência.

## groups_2024.csv

kind identifica maternal_age ou birth_place. name preserva a categoria ou idade da fonte. estimated_births e rate mantêm as unidades anteriores. source_table identifica 1.3 ou 1.4. Esses grupos são recortes nacionais separados, não microdados nem cruzamentos com os municípios.

## Versões e leitura

Os CSVs usam UTF-8, vírgula como delimitador e ponto decimal. Para importar no Excel em português, escolha Dados → De Texto/CSV e confira o separador e a interpretação decimal. Valores vazios significam ausência. A data de consulta e os hashes estão em data/sources.json. Pequenas diferenças nas somas decorrem da precisão dos valores publicados; o Brasil publicado é a referência principal.

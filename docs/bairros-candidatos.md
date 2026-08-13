# Bairros candidatos (referência: MASP)

Levantamento feito em 12/08/2026 direto no QuintoAndar, com os filtros atuais do
`config.py`: aluguel de R$ 500 a R$ 3.000, área de 10 a 50 m².

- **Todos os 31 slugs testados existem** no QuintoAndar (nenhuma URL quebrada).
- A coluna "imóveis no filtro" é o total que o próprio site anuncia **já filtrado**.
  Confirmado: Bela Vista mostra 6.143 sem filtro e 1.101 com filtro; Vila Madalena,
  2.990 e 90.
- Distância em linha reta do centro do bairro (geocodificado no Nominatim) até o MASP.

## Já cadastrados no banco (base de comparação)

| bairro | km até o MASP | imóveis no filtro |
|---|---:|---:|
| Vila Mariana | 3,4 | 591 |
| Chácara Klabin | 4,3 | 326 |
| Pinheiros | 4,8 | 110 |
| Jardim São Paulo | 8,6 | 581 |

## Candidatos, do mais perto ao mais longe

| bairro | slug | km até o MASP | imóveis no filtro |
|---|---|---:|---:|
| Consolação | `consolacao` | 0,6 | 983 |
| Bela Vista | `bela-vista` | 0,6 | 1101 |
| Jardim Paulista | `jardim-paulista` | 0,6 | 399 |
| Bixiga | `bixiga` | 1,0 | 687 |
| Cerqueira César | `cerqueira-cesar` | 1,0 | 271 |
| Higienópolis | `higienopolis` | 1,4 | 857 |
| Jardim América | `jardim-america` | 1,9 | 71 |
| República | `republica` | 2,2 | 1091 |
| Paraíso | `paraiso` | 2,2 | 221 |
| Liberdade | `liberdade` | 2,5 | 1211 |
| Sumaré | `sumare` | 2,5 | 154 |
| Aclimação | `aclimacao` | 3,0 | 510 |
| Santa Cecília | `santa-cecilia` | 3,5 | 1027 |
| Itaim Bibi | `itaim-bibi` | 3,5 | 32 |
| Perdizes | `perdizes` | 3,6 | 396 |
| Vila Madalena | `vila-madalena` | 4,0 | 90 |
| Vila Clementino | `vila-clementino` | 4,3 | 241 |
| Pompeia | `pompeia` | 4,5 | 333 |
| Alto de Pinheiros | `alto-de-pinheiros` | 5,4 | 91 |
| Mirandópolis | `mirandopolis` | 5,4 | 197 |
| Ipiranga | `ipiranga` | 6,0 | 864 |
| Vila Gumercindo | `vila-gumercindo` | 6,0 | 249 |
| Saúde | `saude` | 6,1 | 215 |
| Carandiru | `carandiru` | 6,5 | 426 |
| Butantã | `butanta` | 7,4 | 354 |
| Água Fria | `agua-fria` | 9,3 | 489 |
| Tucuruvi | `tucuruvi` | 10,5 | 291 |
| Mandaqui | `mandaqui` | 10,9 | 230 |
| Cambuci | `cambuci` | não medido | 961 |
| Santana | `santana` | não medido | 786 |

Cambuci e Santana: o Nominatim não devolveu coordenada para o nome do bairro em
nenhuma das tentativas. Pela vizinhança já medida, Cambuci fica em torno de 3 km
(entre Liberdade e Ipiranga) e Santana em torno de 7 km (entre Carandiru e Água Fria).

## Filtro: estação da Linha 1-Azul ou 5-Lilás a até 1 km

Distância medida do centro do bairro até a estação mais próxima, usando as coordenadas
reais das 39 estações dessas duas linhas (fonte: `transit.json` do próprio projeto; a
associação estação-linha foi feita por geometria, checando quais estações encostam no
traçado de cada linha).

| bairro | km até a estação | estação | linha | imóveis no filtro |
|---|---:|---|---|---:|
| Paraíso | 0,01 | Paraíso | Azul | 221 |
| Chácara Klabin *(cadastrado)* | 0,03 | Chácara Klabin | Lilás | 326 |
| Carandiru | 0,04 | Carandiru | Azul | 426 |
| Tucuruvi | 0,21 | Tucuruvi | Azul | 291 |
| Vila Clementino | 0,22 | Hospital São Paulo | Lilás | 241 |
| Jardim São Paulo *(cadastrado)* | 0,24 | Jd. São Paulo-Ayrton Senna | Azul | 581 |
| Mirandópolis | 0,52 | Praça da Árvore | Azul | 197 |
| Saúde | 0,55 | Saúde-Ultrafarma | Azul | 215 |
| Vila Mariana *(cadastrado)* | 0,63 | Ana Rosa | Azul | 591 |
| ~~República~~ *(descartado)* | 0,84 | São Bento | Azul | 1091 |
| ~~Liberdade~~ *(descartado)* | 0,86 | Vergueiro | Azul | 1211 |
| Bixiga | 0,94 | São Joaquim | Azul | 687 |

República e Liberdade foram descartados por decisão do usuário, pela proximidade com a
região central onde circulam usuários de crack. Ver a seção seguinte.

Ficaram de fora por passar de 1 km: Bela Vista (1,18), Aclimação (1,35), Água Fria (1,44),
Vila Gumercindo (1,65), Higienópolis (1,82), Santa Cecília (1,92), Consolação (2,28),
Cambuci (2,56), Ipiranga (2,56), Itaim Bibi (2,72), Cerqueira César (2,77), Jardim América
(3,24), Mandaqui (4,06), Sumaré (4,15), Perdizes (4,71), Pompeia (5,19), Vila Madalena
(5,62), Alto de Pinheiros (7,17), Butantã (7,18).

**Pinheiros, que está cadastrado, não passa neste filtro**: fica a 5,73 km da estação
Azul/Lilás mais próxima, porque é servido pela Linha 4-Amarela.

Santana e Jardim Paulista não tiveram a coordenada resolvida pelo Nominatim. No caso de
Santana, a estação Santana (Azul) fica dentro do bairro, então na prática ele atende.

A medição parte do centro do bairro. Em bairros grandes, boa parte da área pode estar
dentro de 1 km mesmo com o centro fora: a Bela Vista aparece com 1,18 km, mas sua metade
leste (o Bixiga) está a 0,94 km de São Joaquim.

## Segurança

Não existe um índice oficial de "bairro seguro para uma mulher morar". O que há são dados
de ocorrências registradas, e eles precisam ser lidos com cuidado: distrito central com
muita gente circulando registra mais roubo de rua sem que a parte residencial seja pior.

Dado mais recente disponível em agosto de 2026: no primeiro semestre de 2026, o roubo de
celular caiu 14,8% na capital, e apenas 18 distritos policiais tiveram alta. Entre os
bairros deste levantamento, apareceram na lista de **alta**:

| distrito policial | alta no 1º sem. 2026 |
|---|---:|
| 14º DP Pinheiros | +17,8% |
| 15º DP Itaim Bibi | +10% |
| 04º DP Consolação | +6,6% |
| 05º DP Aclimação | +6% |
| 78º DP Jardins | +5,6% |

Nenhum dos 12 bairros da tabela de metrô acima aparece entre os distritos com alta, ou
seja, todos acompanharam a queda geral. O Mapa da Desigualdade 2024 (Rede Nossa São Paulo)
coloca Bela Vista e Vila Mariana entre os melhores indicadores de segurança da cidade.

Ressalva importante: segurança varia por rua e por horário, não por bairro inteiro. Vale
caminhar do imóvel até a estação no mesmo horário em que isso seria feito no dia a dia,
observando iluminação, comércio aberto e movimento de pedestres.

### Região central: onde está o fluxo de usuários de crack em 2026

A concentração histórica de três décadas na Rua dos Protestantes, nos Campos Elísios,
acabou: em 1º de julho de 2026 a prefeitura inaugurou no local a Praça do Triunfo, em
Santa Ifigênia. Isso **não** significa que a questão saiu da região.

O que a imprensa apurou em 2026 é que o fluxo se pulverizou. Em vez de uma concentração
única de cerca de mil pessoas, passaram a circular pequenos grupos por cerca de **260
pontos do distrito de Santa Cecília e arredores**. Dados do governo estadual de 20 a 23 de
abril de 2026 registram média de **214 usuários por turno** na região. Os bairros citados
como afetados pela dispersão são Luz, Campos Elísios, Santa Cecília, Santa Ifigênia e Bom
Retiro, além de pontos no Terminal Princesa Isabel, no Glicério e no Parque Dom Pedro II.
Reportagens registram comércio da região fechando mais cedo por medo.

Distância de cada bairro finalista até o ponto de dispersão mais próximo:

| bairro | km até o ponto mais próximo | ponto |
|---|---:|---|
| ~~República~~ | 1,15 | Rua dos Protestantes |
| ~~Liberdade~~ | 1,53 | Glicério |
| Bixiga | 1,89 | Glicério |
| Carandiru | 2,19 | Bom Retiro |
| Paraíso | 2,76 | Glicério |
| Vila Mariana *(cadastrado)* | 3,42 | Glicério |
| Jardim São Paulo *(cadastrado)* | 4,27 | Bom Retiro |
| Chácara Klabin *(cadastrado)* | 4,40 | Glicério |
| Vila Clementino | 5,19 | Glicério |
| Tucuruvi | 5,97 | Bom Retiro |
| Mirandópolis | 6,27 | Glicério |
| Saúde | 7,04 | Glicério |

Isso confirma o descarte de República (o mais exposto, a pouco mais de 1 km do epicentro
histórico) e de Liberdade, que fica a 1,5 km do Glicério, um dos pontos citados.

Entre os que restaram, o **Bixiga é o mais próximo da área afetada**, a 1,89 km do
Glicério. Uma reportagem também cita a Bela Vista, bairro do qual o Bixiga faz parte, mas
como nova sede de coletivos de redução de danos, ou seja, das organizações que atendem os
usuários, e não como ponto de concentração do fluxo. Vale a decisão consciente.

**Santa Cecília, que aparecia entre os candidatos iniciais, é hoje o centro da dispersão**
e está desaconselhado por este critério, além de já ter ficado fora pela distância do
metrô (1,92 km).

Fontes desta seção:
[Brasil de Fato, dispersão forçada e vigilância](https://www.brasildefato.com.br/2026/03/23/dispersao-forcada-e-vigilancia-o-novo-cenario-da-cracolandia-em-sao-paulo/) ·
[Jornal de Brasília, usuários circulam por 260 pontos da Santa Cecília](https://jornaldebrasilia.com.br/noticias/brasil/apos-esvaziamento-da-cracolandia-usuarios-circulam-por-260-pontos-da-santa-cecilia/) ·
[Metrópoles, antes e depois da Praça do Triunfo](https://www.metropoles.com/sao-paulo/veja-antes-e-depois-da-nova-praca-do-triunfo-onde-ficava-cracolandia) ·
[Terra, usuários se espalham pelo centro e comércio fecha mais cedo](https://www.terra.com.br/noticias/brasil/cidades/cracolandia-usuarios-de-drogas-se-espalham-pelo-centro-de-sp-medo-faz-comercio-fechar-mais-cedo,a49239d791f55f4c53a843151ff4dce776jv73eu.html)

Fontes: [SSP-SP, painel estatístico](https://www.ssp.sp.gov.br/estatistica/painel-estatistico) ·
[Metrópoles, distritos com alta no roubo de celular em 2026](https://www.metropoles.com/sao-paulo/veja-quais-bairros-de-sp-tiveram-aumento-nos-roubos-de-celular-em-2026) ·
[Agência SP, queda dos roubos em 2026](https://www.agenciasp.sp.gov.br/estado-de-sp-tem-queda-inedita-de-todos-os-tipos-de-roubo-no-primeiro-bimestre-de-2026/) ·
[QuintoAndar, bairros mais seguros de SP](https://www.quintoandar.com.br/guias/cidades/bairros-mais-seguros-de-sp/)

## Observações

- **Bixiga é a Bela Vista.** O QuintoAndar mantém os dois slugs e eles se sobrepõem.
  Cadastrar os dois não duplica imóvel no banco (a chave é o id do anúncio), mas gasta
  tempo de coleta à toa. Escolher um.
- Sobreposição parecida, em menor grau: Cerqueira César e Jardim América ficam dentro
  do Jardim Paulista.
- **Oferta baixa demais para valer a coleta**: Itaim Bibi (32), Jardim América (71),
  Vila Madalena (90), Alto de Pinheiros (91). São bairros caros; sobra pouco na faixa
  de até R$ 3.000.

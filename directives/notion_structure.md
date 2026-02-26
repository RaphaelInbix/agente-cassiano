# Estrutura de Saída no Notion

## Formato dos Blocos
Cada post/artigo é salvo como um bloco toggle (`<details>`) contendo:

```
<details>
  <summary><b>Título do Artigo/Post</b></summary>
  <p style="color: gray;">Fonte: Newsletter/Subreddit/Perfil X | Canal: nome_do_canal</p>
  <p>Descrição/resumo do conteúdo curado para o público-alvo</p>
  <p style="color: gray;">Autor: Nome do Autor</p>
  <a href="URL_ORIGINAL">Link para o artigo original</a>
</details>
```

## Campos por Post
| Campo | Descrição | Formato |
|-------|-----------|---------|
| Título | Nome do artigo/post | Negrito no `<summary>` |
| Fonte | Newsletter, subreddit ou perfil X | Texto cinza |
| Canal | Nome específico do canal/sub | Texto cinza |
| Descrição | Resumo curado | Parágrafo dentro do toggle |
| Autor | Quem escreveu | Tag cinza com prefixo "Autor:" |
| Link | URL original do conteúdo | Bookmark ou URL clicável |

## Página de Destino
- **Page ID:** 311621bf-c3ff-80d1-a634-ed2734305ecc
- **Token:** Configurado em config/settings.py

## Organização
- Posts agrupados por seção: Newsletters, Reddit, X
- Ordenados por relevância dentro de cada seção
- Header com data da curadoria semanal

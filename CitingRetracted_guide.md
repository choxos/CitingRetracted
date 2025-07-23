I want to create a database of the paper that have cited retracted papers based on Retraction Watch Database. The database is freely available at Crossref's GitLab repository at https://gitlab.com/crossref/retraction-watch-data.

Here is what I want:
1. Create a web app based on Python and Django.
2. The web app should have the database of all retracted papers. The user can search the database by the title of the retracted paper and the paper's page shows complete metadata + abstract of the retracted paper + reason for retraction and other interesting things if available in Retraction Watch Database.
3. On a place in the retracted paper's page, there should be a box or something to show the papers that have cited the retracted paper.
4. The web app should have analytics page to show the summary of the retracted papers and the papers that have cited the retracted papers.
5. If available, use API of Crossref to get the list of retracted papers. If not, download the data from the GitLab repository and use it (https://gitlab.com/crossref/retraction-watch-data/-/raw/main/retraction_watch.csv?ref_type=heads&inline=false).
6. For retrieving the list of papers that have cited the retracted paper, use OpenAlex API (https://docs.openalex.org/how-to-use-the-api/api-overview).
7. If OpenAlex API is not available, use Semantic Scholar API or OpenCitations API. Search on the web to find the API and how to use it.

Let's GO!
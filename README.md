# Cloud Storage Managed MCP Extension

The Cloud Storage managed MCP extension allows users to manage buckets and
objects via natural language commands.

## Why use the Cloud Storage managed MCP server?

Google and Google Cloud
[managed MCP servers](https://docs.cloud.google.com/mcp/overview) can be used in
your AI applications with enterprise-ready governance, security, and access
control.

## Before you begin

1.  In the Google Cloud console, on the
    [project selector page](https://console.cloud.google.com/projectselector2/home/dashboard),
    select or create a Google Cloud project. > **Note**: If you don't plan to
    keep the resources that you create in this > procedure, create a project
    instead of selecting an existing project. > After you finish these steps,
    you can delete the project, removing all > resources associated with the
    project.
2.  Get your administrator to grant you the
    [MCP Tool User role](https://docs.cloud.google.com/iam/docs/roles-permissions/mcp#mcp.toolUser)
    (`roles/mcp.toolUser`) on the Google Cloud project. If you created a new
    project, then you already have the required permissions.
3.  Ensure your administrator has enabled the
    [Cloud Storage API](https://console.cloud.google.com/marketplace/product/google/storage.googleapis.com)
    on the Google Cloud project.

## Configure authentication

This extension uses Google Application Default Credentials (ADC) to perform
authentication. To login with ADC, run the following command in your terminal:
`bash gcloud auth application-default login`

For additional details, see the
[ADC documentation](https://docs.cloud.google.com/docs/authentication/application-default-credentials#personal).

## Available tools

To see a complete list of available tools and their schemas, see the
[Cloud Storage MCP reference](https://docs.cloud.google.com/storage/docs/reference/mcp).

## Limitations

The Cloud Storage MCP server has the following limitations:

-   **File types**: Read operations for content analysis are restricted to text,
    PDF, and image files; write operations are restricted to text files.
-   **File size**: Maximum of 8 MiB for read and write operations.
-   **Endpoint**: Global endpoint only.

For detailed information on quotas and limits that apply to the Cloud Storage
MCP server, see
[Quotas and limits](https://docs.cloud.google.com/storage/quotas#gcs-mcp).

## Sample use cases

The following are example use cases for the Cloud Storage MCP server.

### Manage retail content and campaigns

A sample use case for the Cloud Storage MCP server is to assist a retailer's
marketing agent to create and manage product listings and promotional campaigns.
The Cloud Storage MCP server lets you list, read, and write objects, and create
buckets for storing product and campaign assets by using natural language.

**Sample prompt**:

"Create a product listing for SKU-123 using assets from the product-images
bucket, then create a new bucket called campaign-q3-assets and generate and save
banner images into it."

**Workflow**: The workflow for creating product listings and campaigns might
look like the following:

-   **List assets**: The agent uses list_objects to find all images for the new
    product in a dedicated Cloud Storage bucket.
-   **Fetch content**: The agent uses read_object to access product assets (up
    to 8 MiB in size), and also fetches product descriptions from a product
    information management (PIM) system using another tool. Generate listing:
    The agent generates a draft of the product listing, including marketing copy
    and links to the images and videos.
-   **Create campaign bucket**: The agent uses create_bucket to create a new
    bucket for campaign assets. Save campaign assets: The agent generates
    campaign assets (for example, banners) and uses write_text to save them into
    the new "campaigns" bucket. Each asset must be less than 8 MiB in size.

### Analyze financial data

A sample use case for the Cloud Storage MCP server is to help portfolio managers
gain insights from financial reports and audio recordings of trader calls with
clients. The Cloud Storage MCP server helps the agent to identify and download
relevant documents and pass them to an LLM for analysis.

**Sample prompt**:

"What were the key takeaways from ExampleCorp's most recent earnings call, and
how does that compare to the sentiment in their last three financial reports?"

**Workflow**: The workflow for analyzing financial documents might look like the
following:

-   **Identify documents**: The agent extracts keywords from the user's question
    to identify relevant buckets or prefixes, for example,
    earnings-calls/ExampleCorp/ or financial-reports/ExampleCorp/ and uses
    list_objects to find relevant audio transcripts and financial reports.
-   **Download content**: The agent uses read_text or read_object to download
    the content of the identified files, up to 8 MiB per file.
-   **Analyze and respond**: The agent passes the content to an LLM to summarize
    findings, compare sentiment, and synthesize an answer to the user's
    question. If needed, other tools like BigQuery can be used for deeper
    analysis.

### Assess vendor risk

A sample use case for the Cloud Storage MCP server is to help automate the
initial vendor risk assessment process for a bank's risk management team. The
Cloud Storage MCP server lets the AI agent fetch and analyze documents that
vendors submit to identify potential risks by using natural language.

**Sample prompt**:

"Assess vendor 'Example Inc.' by reviewing their latest security questionnaire
and compliance certificate in the vendor-docs bucket. Summarize any potential
risks based on our policies and save the report."

**Workflow**: The workflow for assessing vendor risk might look like the
following:

-   **Find documents**: The agent uses the list_objects tool to find the
    vendor's folder in a Cloud Storage bucket dedicated to vendor documents.
-   **Download documents**: The agent uses read_object to download all relevant
    documents, such as security questionnaires, compliance certificates, and
    financial statements, up to 8 MiB per file.
-   **Analyze documents**: The agent analyzes the content of these documents,
    possibly using other tools to extract text, to look for red flags or missing
    information based on the bank's risk policies.
-   **Compile and save report**: The agent compiles a summary report of its
    findings and uses write_text to save it to the vendor's folder in Cloud
    Storage for the risk assessor to review.

## Optional security and safety configurations

MCP introduces new security risks and considerations due to the wide variety of
actions that you can take with MCP tools. To minimize and manage these risks,
Google Cloud offers defaults and customizable policies to control the use of MCP
tools in your Google Cloud organization or project. For more information about
MCP security and governance, see
[AI security and safety](https://docs.cloud.google.com/mcp/ai-security-safety).

## Quotas and limits

The Cloud Storage MCP server doesn't have its own quotas. There is no limit on
the number of calls that can be made to the MCP server. You are still subject to
the quotas enforced by the APIs called by the MCP server tools.

## Reference and resources

*   Explore the
    [Cloud Storage remote MCP server reference documentation](https://docs.cloud.google.com/storage/docs/reference/mcp),
    which includes a list of all available tools, and the full input and output
    schema for each tool.
*   See the
    [Cloud Storage overview](https://docs.cloud.google.com/storage/docs/introduction).
*   Learn about
    [MCP security and governance](https://docs.cloud.google.com/mcp/ai-security-safety).

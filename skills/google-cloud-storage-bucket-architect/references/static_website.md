# Static Website Hosting

This reference document outlines the configuration mapping and architecture
recommendation for Google Cloud Storage buckets configured to host static
websites.

## Description

The user is deploying a static website (HTML, CSS, JavaScript, media assets)
directly to Google Cloud Storage. The site needs to be publicly accessible,
support custom domain mapping, scale automatically for viral traffic spikes, and
serve assets with low latency without backend servers.

## Bucket Configuration Plan Mapping

The following table maps the Static Website Hosting use case to specific GCS
features and details their recommendation status.

| Feature Group  | GCS Feature /   | Status       | Recommendations &            | Documentation Link                                                                    |
:                : Setting         :              : Implementation Details       :                                                                                       :
| :------------- | :-------------- | :----------- | :--------------------------- | :------------------------------------------------------------------------------------ |
| **Core**       | **Storage       | Highly       | **Standard** Storage         | [Storage Classes](https://cloud.google.com/storage/docs/storage-classes)              |
:                : Class**         : Recommended  : Class.<br><br>Required for   :                                                                                       :
:                :                 :              : web serving to ensure        :                                                                                       :
:                :                 :              : immediate, low-latency, and  :                                                                                       :
:                :                 :              : high-throughput asset        :                                                                                       :
:                :                 :              : delivery. Colder tiers must  :                                                                                       :
:                :                 :              : be avoided due to retrieval  :                                                                                       :
:                :                 :              : fees.                        :                                                                                       :
|                | **Bucket Type** | Highly       | **Multi-Regional (MR)**.     | [Locations](https://cloud.google.com/storage/docs/locations)                          |
:                :                 : Recommended  : Distributes website content  :                                                                                       :
:                :                 :              : globally to ensure high      :                                                                                       :
:                :                 :              : availability and low latency :                                                                                       :
:                :                 :              : for diverse user locations.  :                                                                                       :
| **Serving**    | **CORS**        | Highly       | Configure CORS if the site   | [CORS](https://cloud.google.com/storage/docs/using-cors)                              |
:                :                 : Recommended  : loads assets from other      :                                                                                       :
:                :                 :              : origins, or if assets from   :                                                                                       :
:                :                 :              : this bucket are queried by   :                                                                                       :
:                :                 :              : external frontends.          :                                                                                       :
|                | **Website       | **Required** | **Configure Website          | [Hosting Static                                                                       |
:                : Settings**      :              : Configuration.** Set the     : Website](https\://cloud.google.com/storage/docs/hosting-static-website)               :
:                :                 :              : `mainPageSuffix` (e.g.       :                                                                                       :
:                :                 :              : `index.html`) and            :                                                                                       :
:                :                 :              : `notFoundPage` (e.g.         :                                                                                       :
:                :                 :              : `404.html`) to handle root   :                                                                                       :
:                :                 :              : requests and errors.         :                                                                                       :
| **Security**   | **Uniform       | **Required** | **Must be enabled.**         | [Uniform Bucket-Level                                                                 |
:                : Bucket-Level    :              : Standardizes IAM permissions : Access](https\://cloud.google.com/storage/docs/uniform-bucket-level-access)           :
:                : Access (UBLA)** :              : across the bucket.           :                                                                                       :
|                | **Public Access | **Disabled** | **Must be set to "inherited" | [Public Access                                                                        |
:                : Prevention      : (Exception)  : / Disabled.** Public access  : Prevention](https\://cloud.google.com/storage/docs/public-access-prevention)<br>[Make :
:                : (PAP)**         :              : must be allowed to serve web : Bucket                                                                                :
:                :                 :              : traffic. Grant               : Public](https\://cloud.google.com/storage/docs/access-control/making-data-public)     :
:                :                 :              : `roles/storage.objectViewer` :                                                                                       :
:                :                 :              : to `allUsers` to make assets :                                                                                       :
:                :                 :              : publicly accessible.         :                                                                                       :
|                | **Soft Delete** | Good to Have | Enabled as a critical        | [Soft Delete](https://cloud.google.com/storage/docs/soft-delete)                      |
:                :                 :              : rollback mechanism. Helps    :                                                                                       :
:                :                 :              : restore website files        :                                                                                       :
:                :                 :              : quickly if deleted by broken :                                                                                       :
:                :                 :              : build/deploy scripts.        :                                                                                       :
|                | **Object        | Good to Have | Alternative to Soft Delete.  | [Object Versioning](https://cloud.google.com/storage/docs/object-versioning)          |
:                : Versioning**    :              : Allows rolling back bad      :                                                                                       :
:                :                 :              : deployments to a prior known :                                                                                       :
:                :                 :              : good state, but requires OLM :                                                                                       :
:                :                 :              : to prune history.            :                                                                                       :
|                | **IP            | Optional     | Use only if you must limit   | [Bucket IP Filtering](https://cloud.google.com/storage/docs/ip-filtering-overview)    |
:                : Filtering**     :              : access to specific IP ranges :                                                                                       :
:                :                 :              : (including countries or      :                                                                                       :
:                :                 :              : corporate networks, e.g.     :                                                                                       :
:                :                 :              : staging site).               :                                                                                       :
| **Cost**       | **Object        | Highly       | If Versioning is enabled,    | [Lifecycle Management](https://cloud.google.com/storage/docs/lifecycle)               |
:                : Lifecycle       : Recommended  : set lifecycle rules to prune :                                                                                       :
:                : Management      :              : non-current versions (e.g.,  :                                                                                       :
:                : (OLM)**         :              : after 30 days) to prevent    :                                                                                       :
:                :                 :              : old builds from increasing   :                                                                                       :
:                :                 :              : storage bills. Recommend     :                                                                                       :
:                :                 :              : standard OLM                 :                                                                                       :
:                :                 :              : rule\:<br>Transition to      :                                                                                       :
:                :                 :              : `ARCHIVE` after 365 days.    :                                                                                       :
| **Management** | **Labels &      | Good to Have | Apply environment tags       | [Bucket Labels](https://cloud.google.com/storage/docs/using-bucket-labels)            |
:                : Tagging**       :              : (e.g., `{"environment"\:     :                                                                                       :
:                :                 :              : "production"}`).             :                                                                                       :
| **Transfers**  | **Storage       | Good to Have | Replicate site assets closer | [Storage Transfer Service](https://cloud.google.com/storage-transfer/docs/overview)   |
:                : Transfer        :              : to compute regions using     :                                                                                       :
:                : Service (STS)** :              : STS.                         :                                                                                       :
| **Monitoring** | **Cloud         | Highly       | Enable logs to analyze web   | [Cloud Audit Logging](https://cloud.google.com/storage/docs/audit-logging)            |
:                : Logging**       : Recommended  : usage stats, referral paths, :                                                                                       :
:                :                 :              : and user-agent data.         :                                                                                       :
|                | **Cloud         | Highly       | Setup alerts on public       | [Cloud Monitoring](https://cloud.google.com/storage/docs/monitoring)                  |
:                : Monitoring**    : Recommended  : egress, total operations,    :                                                                                       :
:                :                 :              : and error rates (e.g.,       :                                                                                       :
:                :                 :              : 404/503).                    :                                                                                       :
|                | **Pub/Sub       | Good to Have | Trigger downstream workflows | [Pub/Sub Notifications](https://cloud.google.com/storage/docs/pubsub-notifications)   |
:                : Notifications** :              : (such as clearing a CDN      :                                                                                       :
:                :                 :              : cache) whenever `index.html` :                                                                                       :
:                :                 :              : or other assets are updated. :                                                                                       :

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

The following table maps the Static Website Hosting use case to specific Cloud
Storage features and details their recommendation status.

| Feature Group  | Cloud Storage   | Status       | Recommendations &            | Documentation Link                                                                                |
:                : Feature /       :              : Implementation Details       :                                                                                                   :
:                : Setting         :              :                              :                                                                                                   :
| :------------- | :-------------- | :----------- | :--------------------------- | :------------------------------------------------------------------------------------------------ |
| **Core**       | **Storage       | Highly       | **Standard** Storage         | [Storage Classes](https://docs.cloud.google.com/storage/docs/storage-classes.md.txt)              |
:                : Class**         : Recommended  : Class.<br><br>Required for   :                                                                                                   :
:                :                 :              : web serving to ensure        :                                                                                                   :
:                :                 :              : immediate, low-latency, and  :                                                                                                   :
:                :                 :              : high-throughput asset        :                                                                                                   :
:                :                 :              : delivery. Colder tiers must  :                                                                                                   :
:                :                 :              : be avoided due to retrieval  :                                                                                                   :
:                :                 :              : fees.                        :                                                                                                   :
|                | **Bucket Type** | Highly       | **Multi-Regional (MR)**.     | [Locations](https://docs.cloud.google.com/storage/docs/locations.md.txt)                          |
:                :                 : Recommended  : Distributes website content  :                                                                                                   :
:                :                 :              : globally to ensure high      :                                                                                                   :
:                :                 :              : availability and low latency :                                                                                                   :
:                :                 :              : for diverse user locations.  :                                                                                                   :
| **Serving**    | **CORS**        | Highly       | Configure CORS if the site   | [CORS](https://docs.cloud.google.com/storage/docs/using-cors.md.txt)                              |
:                :                 : Recommended  : loads assets from other      :                                                                                                   :
:                :                 :              : origins, or if assets from   :                                                                                                   :
:                :                 :              : this bucket are queried by   :                                                                                                   :
:                :                 :              : external frontends.          :                                                                                                   :
|                | **Website       | **Required** | **Configure Website          | [Hosting Static                                                                                   |
:                : Settings**      :              : Configuration.** Set the     : Website](https\://docs.cloud.google.com/storage/docs/hosting-static-website.md.txt)               :
:                :                 :              : `mainPageSuffix` (e.g.       :                                                                                                   :
:                :                 :              : `index.html`) and            :                                                                                                   :
:                :                 :              : `notFoundPage` (e.g.         :                                                                                                   :
:                :                 :              : `404.html`) to handle root   :                                                                                                   :
:                :                 :              : requests and errors.         :                                                                                                   :
| **Security**   | **Uniform       | **Required** | **Must be enabled.**         | [Uniform Bucket-Level                                                                             |
:                : Bucket-Level    :              : Standardizes IAM permissions : Access](https\://docs.cloud.google.com/storage/docs/uniform-bucket-level-access.md.txt)           :
:                : Access (UBLA)** :              : across the bucket.           :                                                                                                   :
|                | **Public Access | **Disabled** | **Must be set to "inherited" | [Public Access                                                                                    |
:                : Prevention      : (Exception)  : / Disabled.** Public access  : Prevention](https\://docs.cloud.google.com/storage/docs/public-access-prevention.md.txt)<br>[Make :
:                : (PAP)**         :              : must be allowed to serve web : Bucket                                                                                            :
:                :                 :              : traffic. Grant               : Public](https\://docs.cloud.google.com/storage/docs/access-control/making-data-public.md.txt)     :
:                :                 :              : `roles/storage.objectViewer` :                                                                                                   :
:                :                 :              : to `allUsers` to make assets :                                                                                                   :
:                :                 :              : publicly accessible.         :                                                                                                   :
|                | **Soft Delete** | Good to Have | Enabled as a critical        | [Soft Delete](https://docs.cloud.google.com/storage/docs/soft-delete.md.txt)                      |
:                :                 :              : rollback mechanism. Helps    :                                                                                                   :
:                :                 :              : restore website files        :                                                                                                   :
:                :                 :              : quickly if deleted by broken :                                                                                                   :
:                :                 :              : build/deploy scripts.        :                                                                                                   :
|                | **Object        | Good to Have | Alternative to Soft Delete.  | [Object Versioning](https://docs.cloud.google.com/storage/docs/object-versioning.md.txt)          |
:                : Versioning**    :              : Allows rolling back bad      :                                                                                                   :
:                :                 :              : deployments to a prior known :                                                                                                   :
:                :                 :              : good state, but requires OLM :                                                                                                   :
:                :                 :              : to prune history.            :                                                                                                   :
|                | **IP            | Optional     | Use only if you must limit   | [Bucket IP Filtering](https://docs.cloud.google.com/storage/docs/ip-filtering-overview.md.txt)    |
:                : Filtering**     :              : access to specific IP ranges :                                                                                                   :
:                :                 :              : (including countries or      :                                                                                                   :
:                :                 :              : corporate networks, e.g.     :                                                                                                   :
:                :                 :              : staging site).               :                                                                                                   :
| **Cost**       | **Object        | Highly       | If Versioning is enabled,    | [Lifecycle Management](https://docs.cloud.google.com/storage/docs/lifecycle.md.txt)               |
:                : Lifecycle       : Recommended  : set lifecycle rules to prune :                                                                                                   :
:                : Management      :              : non-current versions (e.g.,  :                                                                                                   :
:                : (OLM)**         :              : after 30 days) to prevent    :                                                                                                   :
:                :                 :              : old builds from increasing   :                                                                                                   :
:                :                 :              : storage bills. Recommend     :                                                                                                   :
:                :                 :              : standard OLM                 :                                                                                                   :
:                :                 :              : rule\:<br>Transition to      :                                                                                                   :
:                :                 :              : `ARCHIVE` after 365 days.    :                                                                                                   :
| **Management** | **Labels &      | Good to Have | Apply environment tags       | [Bucket Labels](https://docs.cloud.google.com/storage/docs/using-bucket-labels.md.txt)            |
:                : Tagging**       :              : (e.g., `{"environment"\:     :                                                                                                   :
:                :                 :              : "production"}`).             :                                                                                                   :
| **Transfers**  | **Storage       | Good to Have | Replicate site assets closer | [Storage Transfer Service](https://docs.cloud.google.com/storage-transfer/docs/overview.md.txt)   |
:                : Transfer        :              : to compute regions using     :                                                                                                   :
:                : Service (STS)** :              : STS.                         :                                                                                                   :
| **Monitoring** | **Cloud         | Highly       | Enable logs to analyze web   | [Cloud Audit Logging](https://docs.cloud.google.com/storage/docs/audit-logging.md.txt)            |
:                : Logging**       : Recommended  : usage stats, referral paths, :                                                                                                   :
:                :                 :              : and user-agent data.         :                                                                                                   :
|                | **Cloud         | Highly       | Setup alerts on public       | [Cloud Monitoring](https://docs.cloud.google.com/storage/docs/monitoring.md.txt)                  |
:                : Monitoring**    : Recommended  : egress, total operations,    :                                                                                                   :
:                :                 :              : and error rates (e.g.,       :                                                                                                   :
:                :                 :              : 404/503).                    :                                                                                                   :
|                | **Pub/Sub       | Good to Have | Trigger downstream workflows | [Pub/Sub Notifications](https://docs.cloud.google.com/storage/docs/pubsub-notifications.md.txt)   |
:                : Notifications** :              : (such as clearing a CDN      :                                                                                                   :
:                :                 :              : cache) whenever `index.html` :                                                                                                   :
:                :                 :              : or other assets are updated. :                                                                                                   :

Terraform project to create the necessary infrastructure to get Kspyder up and running on Azure Function Apps.

Contents (roughly) :
- An Azure Function App, with one additional Development slot for testing environment
- An Azure MSSQL Server
- Two Azure SQL databases within the server : one for PROD, one for DEV and testing
- An Azure Key Vault to store all app credentials
- The necessary networking around that : one vnet, one subnet, one IP Address and one NAT gateway to force all incoming AND outgoing traffic into a single fixed IP

Variables are up to you :)
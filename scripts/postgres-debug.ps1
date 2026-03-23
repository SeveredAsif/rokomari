param(
    [ValidateSet("logs", "shell", "psql")]
    [string]$Action = "logs"
)

$ContainerName = "rokomari-postgres"

switch ($Action) {
    "logs" {
        docker logs -f $ContainerName
    }
    "shell" {
        docker exec -it $ContainerName sh
    }
    "psql" {
        docker exec -it $ContainerName psql -U postgres -d rokomari
    }
}

kubectl create secret generic basic-auth --from-file=auth -n tradingbot22  

## velero backup 

velero schedule create tradingbot22-backup --schedule="0 2 * * 1" --include-namespaces=tradingbot22
velero backup create --from-schedule tradingbot22-backup

kubectl create secret generic s3backuptarget --from-env-file=s3backup -n tradingbot22
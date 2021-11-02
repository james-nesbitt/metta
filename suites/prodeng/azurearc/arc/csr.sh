
kubectl apply -f csr.yaml

kubectl create clusterrolebinding privileged2 --clusterrole=psp:privileged --serviceaccount azure-arc:azure-arc-kube-aad-proxy-sa --serviceaccount sonobuoy:sonobuoy-serviceaccount --serviceaccount default:default --serviceaccount arc-k8s-demo:default

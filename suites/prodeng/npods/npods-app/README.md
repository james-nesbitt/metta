# N-Pods

A simple app that can be used to measure how many pods can be run on a node.

## Methodology

The process is a simple relay.  The app is deployed as a scalable kubernetes
deployment with an internal network service. The app itself receives an http
request which it then relays to the service to continue the relay. This creates
an infinite linear relay.

To trigger the relay any single http request to the relay service wil start a
relay thread.

## The app

The app is a small golang http server app that waits for an http request, and
then relays that request to the service. The app does reply to the request and
run the relay in separate goroutines to avoid keeping http sessions open.

If the thread receives a `pass` query argument, then it will increment it and
pass it onto the next relay.
If the thread receives a `thread` query argument then it will pass it on to the
next relay unchanged.  This allows multiple concurrent thread to be triggered
while keeping their logging identifiable.

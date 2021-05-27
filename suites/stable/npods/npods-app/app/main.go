package main

import (
	"crypto/rand"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"
)

const (
	RELAY_ENDPOINT_DEFAULT  = "/"
	RELAY_LISTEN_DEFAULT    = ":80"
	RELAY_NEXT_URI_ENV      = "NPODS_NEXT_URI"
	RELAY_REPEAT_DELAY_SECS = 1
)

var (
	relayEndpoint string
	relayListen   string
	nextURL       *url.URL
	hostname      string
)

func init() {
	hostname, _ = os.Hostname()

	// Decide on http endpoint for relay
	relayEndpoint = RELAY_ENDPOINT_DEFAULT

	// Decide on http listen
	relayListen = RELAY_LISTEN_DEFAULT

	// get Next URI from ENV
	if envNext := os.Getenv(RELAY_NEXT_URI_ENV); envNext != "" {
		if nextURLTemp, err := url.ParseRequestURI(envNext); err == nil {
			nextURL = nextURLTemp
			fmt.Println("Next URL set as ", nextURL.String())
		}
	} else {
		fmt.Println("No next URL set")
		os.Exit(1)
	}
}

// Main execution method
func main() {
	http.HandleFunc(relayEndpoint, Relay)
	log.Fatal(http.ListenAndServe(relayListen, nil))
}

// Relay an http request to the next app in the cluster
func Relay(w http.ResponseWriter, r *http.Request) {
	// Copy of URL so that we can modify without changing
	thisNextURL, _ := url.Parse(nextURL.String())
	referer := r.RemoteAddr
	query := r.URL.Query()

	m := map[string]string{
		"when": time.Now().String(),
		"me":   hostname,
		"from": referer,
		"request": r.URL.String(),
	}

	// some relay metadata detection
	var pass int
	if qpass, err := fromIntQuery(query, "pass"); err == nil {
		pass = qpass
	} else {
		pass = 0
	}
	pass = pass + 1
	m["pass"] = strconv.Itoa(pass)
	query.Set("pass", strconv.Itoa(pass))

	var thread string
	if qthread, err := fromQuery(query, "thread"); err == nil {
		thread = qthread
		query.Set("thread", thread)
	} else {
		thread = "none"
	}
	m["thread"] = thread
	query.Set("thread", thread)

	// Workload detection and execution

	if sleep, err := fromEnvValue("sleep"); err == nil {
		if dur, errd := time.ParseDuration(sleep); errd == nil {
			m["sleep"] = sleep
			workloadWait(dur)
		} else {
			fmt.Printf("Bad sleep workload request value, need integer seconds: ", errd)
		}
	}

	if cpu, err := fromEnvValue("cpu"); err == nil {
		if cpui, erri := strconv.Atoi(cpu); erri == nil {
			m["cpu"] = cpu
			workloadCPU(cpui)
		} else {
			fmt.Printf("Bad CPU workload request value, need integer: ", erri)
		}
	}

	if ram, err := fromEnvValue("ram"); err == nil {
		if rami, erri := strconv.Atoi(ram); erri == nil {
			m["ram"] = ram
			workloadRAM(rami)
		} else {
			fmt.Printf("Bad RAM workload request value, need integer: ", erri)
		}
	}

	// requild the URL query with any changes added
	thisNextURL.RawQuery = query.Encode()

	// output message json to reponse and console.
	mb, _ := json.Marshal(m)
	fmt.Println(string(mb))
	w.WriteHeader(200)
	w.Write(mb)

	// Send out the relay ping in a subroutine so that it doesn't block return
	go func(next *url.URL) {
		client := http.Client{
			Timeout: 15 * time.Second,
		}
		request := http.Request{
			Host:   hostname,
			Close:  true,
			URL:    next,
			Method: "GET",
		}
		for {
			if _, err := client.Do(&request); err == nil {
				break
			} else {
				fmt.Println("Could not relay, will try again: ", err)
			}
			time.Sleep(RELAY_REPEAT_DELAY_SECS)
		}
	}(thisNextURL)
}

// Workloads

// workload that waits for duration string
func workloadWait(dur time.Duration) {
	time.Sleep(dur)
}

// workload which runs a crypto rand CPU intensive operation
func workloadCPU(num int) {
	// fill a 1000 byte array num times.  This makes it more CPU and less
	// RAM oriented
	b := make([]byte, 1)
	for i := 0; i < num; i++ {
		rand.Read(b)
	}
}

// workload which creates memory structures to occupy and release RAM
func workloadRAM(num int) []byte {
	return make([]byte, num)
}

// workload that

// Utility

// Retrieve the last matching query argument as an integer
func fromIntQuery(q url.Values, name string) (int, error) {
	if val, err := fromQuery(q, name); err == nil {
		return strconv.Atoi(val)
	} else {
		return 0, err
	}
}

// Retrieve the last matching query argument
func fromQuery(q url.Values, name string) (string, error) {
	if vals, ok := q[name]; ok && len(vals) > 0 {
		// get the last provided query thread value (there may be many)
		return vals[len(vals)-1], nil
	} else {
		return "", fmt.Errorf("No matching value")
	}
}

// Retrieve value from ENV Variable standardizing ENV VAR NAMES
func fromEnvValue(name string) (string, error) {
	name = fmt.Sprintf("TEST_%s", strings.ToUpper(name))
	if value, ok := os.LookupEnv(name); ok {
		return value, nil
	} else {
		return "", fmt.Errorf("No such var")
	}
}

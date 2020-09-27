package main

import (
	"flag"
	"log"
	"net/http"
	"time"
)

func logMiddleware(h http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		h.ServeHTTP(w, r)
		duration := float64(time.Since(start)) / float64(time.Millisecond)
		log.Printf("%s %s %fms", r.Method, r.RequestURI, duration)
	})
}

func main() {
	port := flag.String("p", "9000", "port to serve on")
	directory := "./docs"
	flag.Parse()

	fs := http.FileServer(http.Dir(directory))
	http.Handle("/", logMiddleware(fs))

	log.Printf("Serving %s on HTTP port: %s\n", directory, *port)
	log.Fatal(http.ListenAndServe(":"+*port, nil))
}

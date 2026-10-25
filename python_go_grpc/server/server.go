package main

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"io/ioutil"
	"log"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/oklog/run"
	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/peer"
	"google.golang.org/grpc/status"

	"python_go_grpc/server/api"
)

func loggingInterceptor(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
	ts := time.Now()

	peer, ok := peer.FromContext(ctx)
	if !ok {
		return nil, status.Errorf(codes.InvalidArgument, "missing peer")
	}

	md, ok := metadata.FromIncomingContext(ctx)
	if !ok {
		return nil, status.Errorf(codes.InvalidArgument, "missing metadata")
	}

	res, err := handler(ctx, req)

	log.Printf("server=%q ip=%q method=%q status=%s duration=%s user-agent=%q",
		md[":authority"][0],
		peer.Addr.String(),
		info.FullMethod,
		status.FromContextError(err).Code(),
		time.Since(ts),
		md["user-agent"][0],
	)
	return res, err
}

func main() {
	secureAddress := "127.0.0.1:8443"
	insecureAddress := "127.0.0.1:50051"

	var g run.Group

	// Handling signals
	term := make(chan os.Signal, 1)
	signal.Notify(term, syscall.SIGINT, syscall.SIGTERM)
	cancel := make(chan struct{})
	g.Add(
		func() error {
			select {
			case s := <-term:
				log.Printf("Received signal=%q, exiting...", s)
			case <-cancel:
				// pass
			}
			return nil
		},
		func(err error) {
			close(cancel)
		},
	)

	serverCert, err := tls.LoadX509KeyPair("certs/server.pem", "certs/server-key.pem")
	if err != nil {
		log.Printf("failed to load server cert/key: %s", err)
		os.Exit(1)
	}

	caCert, err := ioutil.ReadFile("certs/ca.pem")
	if err != nil {
		log.Printf("failed to load CA cert: %s", err)
		os.Exit(1)
	}
	caCertPool := x509.NewCertPool()
	caCertPool.AppendCertsFromPEM(caCert)

	creds := credentials.NewTLS(&tls.Config{
		Certificates: []tls.Certificate{serverCert},
		ClientCAs:    caCertPool,
		ClientAuth:   tls.RequireAndVerifyClientCert,
	})

	secureSrv := grpc.NewServer(grpc.Creds(creds), grpc.UnaryInterceptor(loggingInterceptor))
	g.Add(
		func() error {
			log.Printf("Starting gRPC server, address=%q", secureAddress)
			lis, err := net.Listen("tcp", secureAddress)
			if err != nil {
				return fmt.Errorf("failed to listen: %w", err)
			}
			api.RegisterDiceServiceServer(secureSrv, api.NewServer())
			if err := secureSrv.Serve(lis); err != nil {
				return fmt.Errorf("failed to serve: %w", err)
			}
			return nil
		},
		func(err error) {
			secureSrv.Stop()
		},
	)

	insecureSrv := grpc.NewServer(grpc.UnaryInterceptor(loggingInterceptor))
	g.Add(
		func() error {
			log.Printf("Starting gRPC server (h2c), address=%q", insecureAddress)
			lis, err := net.Listen("tcp", insecureAddress)
			if err != nil {
				return fmt.Errorf("failed to listen: %w", err)
			}
			api.RegisterDiceServiceServer(insecureSrv, api.NewServer())
			if err := insecureSrv.Serve(lis); err != nil {
				return fmt.Errorf("failed to serve: %w", err)
			}
			return nil
		},
		func(err error) {
			insecureSrv.Stop()
		},
	)

	if err := g.Run(); err != nil {
		log.Print(err)
	}
}

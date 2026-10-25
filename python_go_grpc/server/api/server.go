package api

import (
	"context"
	"math/rand"
	"time"
)

// Number of dots on a die
const Dots = 6

type Server struct {
	UnimplementedDiceServiceServer
	rnd *rand.Rand
}

func NewServer() *Server {
	return &Server{
		rnd: rand.New(rand.NewSource(time.Now().UnixNano())),
	}
}

func (s *Server) RollDie(ctx context.Context, req *RollDieRequest) (*RollDieResponse, error) {
	// rand.Intn returns a value in [0, Dots) interval
	value := s.rnd.Intn(Dots) + 1
	return &RollDieResponse{Value: int32(value)}, nil
}

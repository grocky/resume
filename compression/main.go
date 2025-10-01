package main

import (
	"fmt"
	"log"
	"os"

	"github.com/unidoc/unipdf/v3/common/license"
	"github.com/unidoc/unipdf/v3/model"
	"github.com/unidoc/unipdf/v3/model/optimize"
)

func init() {
	err := license.SetMeteredKey(os.Getenv(`UNIDOC_LICENSE_API_KEY`))
	if err != nil {
		panic(err)
	}
}

func main() {

	args := os.Args
	if len(args) < 3 {
		fmt.Printf("Usage: %s <input.pdf> <output.pdf>\n", args[0])
	}

	inputPath := args[1]
	outputPath := args[2]

	log.Printf("Starting PDF optimization... %s -> %s\n", inputPath, outputPath)

	inputFileInfo, err := os.Stat(inputPath)
	if err != nil {
		log.Fatalf("Error accessing input file: %v", err)
	}

	inputFile, err := os.Open(inputPath)
	if err != nil {
		log.Fatalf("Error opening input file: %v", err)
	}
	defer inputFile.Close()

	reader, err := model.NewPdfReader(inputFile)
	if err != nil {
		log.Fatalf("Error creating PDF reader: %v", err)
	}

	pdfWriter, err := reader.ToWriter(nil)
	if err != nil {
		log.Fatalf("Error creating PDF writer: %v", err)
	}

	pdfWriter.SetOptimizer(optimize.New(optimize.Options{
		CombineDuplicateDirectObjects:   true,
		CombineIdenticalIndirectObjects: true,
		CombineDuplicateStreams:         true,
		CompressStreams:                 true,
		UseObjectStreams:                true,
		ImageQuality:                    100,
		ImageUpperPPI:                   300,
		CleanUnusedResources:            true,
	}))

	err = pdfWriter.WriteToFile(outputPath)
	if err != nil {
		log.Fatalf("Error writing output file: %v", err)
	}

	outputFileInfo, err := os.Stat(outputPath)
	if err != nil {
		log.Fatalf("Error accessing output file: %v", err)
	}

	inputSize := inputFileInfo.Size()
	outputSize := outputFileInfo.Size()
	ratio := 100.0 - (float64(outputSize) / float64(inputFileInfo.Size()) * 100.0)

	fmt.Printf("Optimization complete. Size reduced by %.2f%%\n", ratio)
	fmt.Printf("Input file: %s (%.2f MB)\n", inputPath, float64(inputSize)/(1024*1024))
	fmt.Printf("Output file: %s (%.2f MB)\n", outputPath, float64(outputSize)/(1024*1024))
}

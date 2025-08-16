# MCRDL Language Specification v1.0

## 1. Lexical Structure

### 1.1 Character Set
- ASCII characters (UTF-8 in string literals and comments)
- Case-sensitive identifiers

### 1.2 Comments
```mcrdl
// Single-line comment
/* Multi-line 
   comment */
```

### 1.3 Identifiers
- Start with letter or underscore
- Contain letters, digits, underscores
- Cannot be reserved keywords

### 1.4 Keywords
```
module      input       output      inout       wire
reg         parameter   localparam  assign      always
initial     if          else        case        default
for         while       repeat      forever     delay
posedge     negedge     begin       end         function
task        generate    endgenerate import      export
```

### 1.5 Operators

#### Arithmetic
- `+` Addition
- `-` Subtraction
- `*` Multiplication
- `/` Division
- `%` Modulo
- `**` Power

#### Logical
- `&&` Logical AND
- `||` Logical OR
- `!` Logical NOT

#### Bitwise
- `&` Bitwise AND
- `|` Bitwise OR
- `^` Bitwise XOR
- `~` Bitwise NOT
- `<<` Left shift
- `>>` Right shift

#### Relational
- `==` Equal
- `!=` Not equal
- `<` Less than
- `>` Greater than
- `<=` Less than or equal
- `>=` Greater than or equal

#### Assignment
- `=` Blocking assignment
- `<=` Non-blocking assignment

#### Conditional
- `? :` Ternary operator

### 1.6 Literals

#### Integer Literals
```mcrdl
42          // Decimal
0b1010      // Binary
0o52        // Octal
0x2A        // Hexadecimal
4'b1010     // 4-bit binary
8'hFF       // 8-bit hexadecimal
```

#### String Literals
```mcrdl
"Hello, World!"
"Escaped \"quotes\""
```

#### Time Literals
```mcrdl
10t         // 10 ticks (1 second)
5rt         // 5 redstone ticks (0.5 seconds)
```

## 2. Data Types

### 2.1 Primitive Types

#### wire
Single-bit or multi-bit combinational signal
```mcrdl
wire a;              // Single bit
wire [7:0] bus;      // 8-bit bus
wire [15:0] data;    // 16-bit bus
```

#### reg
Single-bit or multi-bit sequential signal (holds state)
```mcrdl
reg flip_flop;       // Single bit register
reg [3:0] counter;   // 4-bit counter
```

#### analog
Analog signal for comparator operations (0-15)
```mcrdl
analog strength;     // Redstone signal strength
```

#### integer
Compile-time integer for parameters and loops
```mcrdl
integer i;
parameter integer WIDTH = 8;
```

### 2.2 Composite Types

#### Arrays
```mcrdl
wire [7:0] memory [0:255];  // 256 bytes of memory
reg [3:0] registers [8];     // 8 4-bit registers
```

#### Structures
```mcrdl
struct Point {
    wire [7:0] x;
    wire [7:0] y;
}
```

## 3. Module Declaration

### 3.1 Basic Module
```mcrdl
module ModuleName {
    // Port declarations
    input wire a, b;
    output wire result;
    
    // Internal logic
    assign result = a & b;
}
```

### 3.2 Parameterized Module
```mcrdl
module Counter #(
    parameter WIDTH = 8,
    parameter INIT_VALUE = 0
) {
    input wire clock, reset;
    output reg [WIDTH-1:0] count = INIT_VALUE;
    
    always @(posedge clock) {
        if (reset) {
            count <= INIT_VALUE;
        } else {
            count <= count + 1;
        }
    }
}
```

### 3.3 Module Instantiation
```mcrdl
module Top {
    wire clk, rst;
    wire [7:0] count_value;
    
    // Named parameter binding
    Counter #(.WIDTH(8), .INIT_VALUE(0)) counter1 (
        .clock(clk),
        .reset(rst),
        .count(count_value)
    );
    
    // Positional parameter binding
    Counter #(8, 0) counter2 (clk, rst, count_value);
}
```

## 4. Behavioral Constructs

### 4.1 Continuous Assignment
```mcrdl
assign output = input1 & input2;
assign bus = enable ? data : 8'bz;
```

### 4.2 Always Blocks
```mcrdl
// Combinational logic
always @(*) {
    case (select)
        2'b00: out = in0;
        2'b01: out = in1;
        2'b10: out = in2;
        2'b11: out = in3;
        default: out = 0;
    }
}

// Sequential logic
always @(posedge clock or posedge reset) {
    if (reset) {
        state <= IDLE;
    } else {
        state <= next_state;
    }
}

// Timed behavior
always {
    clock = 0;
    delay(5t);
    clock = 1;
    delay(5t);
}
```

### 4.3 Initial Blocks
```mcrdl
initial {
    // Initialization code
    reset = 1;
    delay(10t);
    reset = 0;
}
```

### 4.4 Functions
```mcrdl
function [7:0] add(input [7:0] a, b) {
    return a + b;
}
```

### 4.5 Tasks
```mcrdl
task pulse(output reg signal, input integer duration) {
    signal = 1;
    delay(duration);
    signal = 0;
}
```

## 5. Redstone-Specific Constructs

### 5.1 Component Instantiation
```mcrdl
module Circuit {
    // Redstone components
    redstone_torch torch1 @ (0, 0, 0);
    redstone_repeater rep1 @ (1, 0, 0) facing(EAST) delay(2);
    redstone_comparator comp1 @ (2, 0, 0) mode(SUBTRACT);
    piston piston1 @ (3, 0, 0) facing(UP);
    
    // Wiring
    connect torch1.output -> rep1.input;
    connect rep1.output -> comp1.input_a;
}
```

### 5.2 Placement Constraints
```mcrdl
module Compact {
    constraint area {
        max_width = 10;
        max_height = 5;
        max_depth = 10;
    }
    
    constraint timing {
        max_delay = 20t;
    }
}
```

### 5.3 Power Levels
```mcrdl
module PowerControl {
    analog power_level;
    
    // Set specific power level
    power_level = 15;  // Maximum power
    power_level = 7;   // Half power
    
    // Comparator operations
    if (power_level > 8) {
        // High power actions
    }
}
```

## 6. Timing Specification

### 6.1 Delay Statements
```mcrdl
delay(10t);        // Delay 10 ticks
delay(5rt);        // Delay 5 redstone ticks
```

### 6.2 Timing Constraints
```mcrdl
module FastAdder {
    timing {
        input_to_output_delay < 4rt;
        setup_time = 1rt;
        hold_time = 1rt;
    }
}
```

## 7. Generate Constructs

### 7.1 Generate For
```mcrdl
generate
    for (genvar i = 0; i < 8; i++) {
        wire bit_wire;
        assign bit_wire = data[i] & enable;
    }
endgenerate
```

### 7.2 Generate If
```mcrdl
generate
    if (WIDTH == 8) {
        // 8-bit specific logic
    } else if (WIDTH == 16) {
        // 16-bit specific logic
    }
endgenerate
```

## 8. Preprocessor Directives

```mcrdl
#define MAX_WIDTH 16
#include "stdlib/gates.mcrdl"
#ifdef DEBUG
    // Debug code
#endif
```

## 9. Standard Library Import

```mcrdl
import std.gates.*;
import std.arithmetic.FullAdder;
import std.memory.{DFlipFlop, Register};
```

## 10. Example Programs

### 10.1 Simple AND Gate
```mcrdl
module AndGate {
    input wire a, b;
    output wire out;
    
    // Using built-in operator
    assign out = a & b;
    
    // Or using redstone components
    redstone_torch torch_a @ (0, 0, 0) inverted_by(a);
    redstone_torch torch_b @ (1, 0, 0) inverted_by(b);
    redstone_torch torch_out @ (2, 0, 0) 
        powered_by(!torch_a.output | !torch_b.output);
    
    assign out = torch_out.output;
}
```

### 10.2 4-bit Counter
```mcrdl
module Counter4Bit {
    input wire clock, reset;
    output reg [3:0] count;
    
    always @(posedge clock or posedge reset) {
        if (reset) {
            count <= 4'b0000;
        } else {
            count <= count + 1;
        }
    }
}
```

### 10.3 7-Segment Display Driver
```mcrdl
module SevenSegment {
    input wire [3:0] digit;
    output reg [6:0] segments;
    
    always @(*) {
        case (digit)
            4'h0: segments = 7'b1111110;
            4'h1: segments = 7'b0110000;
            4'h2: segments = 7'b1101101;
            4'h3: segments = 7'b1111001;
            4'h4: segments = 7'b0110011;
            4'h5: segments = 7'b1011011;
            4'h6: segments = 7'b1011111;
            4'h7: segments = 7'b1110000;
            4'h8: segments = 7'b1111111;
            4'h9: segments = 7'b1111011;
            4'hA: segments = 7'b1110111;
            4'hB: segments = 7'b0011111;
            4'hC: segments = 7'b1001110;
            4'hD: segments = 7'b0111101;
            4'hE: segments = 7'b1001111;
            4'hF: segments = 7'b1000111;
            default: segments = 7'b0000000;
        }
    }
}
```

### 10.4 Pulse Generator
```mcrdl
module PulseGen {
    input wire trigger;
    output reg pulse;
    parameter PULSE_WIDTH = 5rt;
    
    always @(posedge trigger) {
        pulse <= 1;
        delay(PULSE_WIDTH);
        pulse <= 0;
    }
}
```

## 11. Grammar (BNF)

```bnf
program ::= module_declaration*

module_declaration ::= 'module' identifier module_parameters? '{' module_body '}'

module_parameters ::= '#(' parameter_list ')'

parameter_list ::= parameter_declaration (',' parameter_declaration)*

parameter_declaration ::= 'parameter' type? identifier '=' expression

module_body ::= module_item*

module_item ::= port_declaration
              | variable_declaration
              | continuous_assignment
              | always_block
              | initial_block
              | module_instantiation
              | function_declaration
              | task_declaration

port_declaration ::= port_direction type identifier_list ';'

port_direction ::= 'input' | 'output' | 'inout'

type ::= 'wire' range?
       | 'reg' range?
       | 'analog'
       | 'integer'

range ::= '[' expression ':' expression ']'

continuous_assignment ::= 'assign' lvalue '=' expression ';'

always_block ::= 'always' sensitivity_list? statement

sensitivity_list ::= '@(' sensitivity_item ('or' sensitivity_item)* ')'
                   | '@(*)'

sensitivity_item ::= 'posedge' identifier
                   | 'negedge' identifier
                   | identifier

statement ::= simple_statement
            | compound_statement
            | conditional_statement
            | case_statement
            | loop_statement

compound_statement ::= '{' statement* '}'

conditional_statement ::= 'if' '(' expression ')' statement ('else' statement)?

case_statement ::= 'case' '(' expression ')' case_item* 'default' ':' statement? '}'

loop_statement ::= 'for' '(' statement expression ';' statement ')' statement
                 | 'while' '(' expression ')' statement
                 | 'repeat' '(' expression ')' statement
                 | 'forever' statement

expression ::= primary_expression
             | unary_expression
             | binary_expression
             | conditional_expression

primary_expression ::= identifier
                     | literal
                     | '(' expression ')'

unary_expression ::= unary_operator expression

binary_expression ::= expression binary_operator expression

conditional_expression ::= expression '?' expression ':' expression
```

## 12. Semantic Rules

1. **Type Compatibility**: Wire and reg types can be mixed in expressions but not in assignments
2. **Bit Width Matching**: Assignments must have matching bit widths or explicit casting
3. **Clock Domain**: All sequential logic in a module must be in the same clock domain
4. **Timing Closure**: All paths must meet timing constraints
5. **Power Budget**: Total power consumption must not exceed limits
6. **Physical Constraints**: Component placement must be physically realizable

## 13. Standard Library

The standard library provides pre-built modules for common circuits:

- `std.gates`: Basic logic gates
- `std.arithmetic`: Arithmetic operations
- `std.memory`: Memory elements
- `std.timing`: Clock and timing utilities
- `std.io`: Input/output interfaces
- `std.redstone`: Redstone-specific components
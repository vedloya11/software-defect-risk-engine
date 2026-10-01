import os
import ast
import math
from typing import Dict, Any, List, Tuple
from radon.complexity import cc_visit
from radon.raw import analyze as raw_analyze
from radon.metrics import h_visit

class SourceCodeAnalyzer:
    """
    Static Code Analysis Engine.
    Parses raw Python source code using AST and Radon to extract
    static software defect metrics compatible with the ML Defect Engine.
    """

    def __init__(self):
        pass

    def analyze_source_code(self, code_str: str, filename: str = "module.py") -> Dict[str, Any]:
        """
        Extracts static code metrics and identifies the most complex/suspicious components.
        """
        if not code_str.strip():
            raise ValueError("Provided source code is empty.")

        # 1. Parse AST to verify syntax and count structural elements
        try:
            tree = ast.parse(code_str, filename=filename)
        except SyntaxError as e:
            raise ValueError(f"Syntax error in code file: {e.msg} at line {e.lineno}")

        # 2. Raw Line Metrics (LOC, LLOC, Comments, Blanks)
        raw_metrics = raw_analyze(code_str)
        loc = max(1, raw_metrics.loc)

        # 3. Cyclomatic Complexity & Most Complex Function
        blocks = cc_visit(code_str)
        total_cyclo = sum(b.complexity for b in blocks) if blocks else 1
        
        # Identify most suspicious (highest complexity) function
        most_suspicious_component = "module_level"
        highest_cyclo = 1
        function_complexities = []

        for b in blocks:
            function_complexities.append({
                "name": b.name,
                "complexity": b.complexity,
                "type": b.__class__.__name__,
                "lineno": b.lineno
            })
            if b.complexity > highest_cyclo:
                highest_cyclo = b.complexity
                most_suspicious_component = f"{b.name}() [Complexity: {b.complexity}, Line {b.lineno}]"

        # 4. Halstead Metrics
        try:
            h_metrics = h_visit(code_str)
            # Total operators (N1) and total operands (N2)
            n1 = h_metrics.total.N1 if hasattr(h_metrics, 'total') else 10
            n2 = h_metrics.total.N2 if hasattr(h_metrics, 'total') else 10
            length = h_metrics.total.length if hasattr(h_metrics, 'total') else (n1 + n2)
            volume = h_metrics.total.volume if hasattr(h_metrics, 'total') else (length * math.log2(max(2, n1 + n2)))
            difficulty = h_metrics.total.difficulty if hasattr(h_metrics, 'total') else 1.0
        except Exception:
            # Fallback estimation if Halstead visit encounters unsupported tokens
            n1 = 15
            n2 = 10
            length = n1 + n2
            volume = length * math.log2(25)
            difficulty = 5.0

        # 5. AST-based Branch Count & Coupling (Fan-In / Fan-Out)
        branch_count = 0
        fan_out_imports = set()
        fan_in_definitions = 0

        for node in ast.walk(tree):
            # Decisions / Branch points
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler, ast.With, ast.Assert)):
                branch_count += 1
            elif isinstance(node, ast.BoolOp):
                # boolean operations like (a and b or c) add branches
                branch_count += len(node.values) - 1
            
            # Fan-Out: External dependencies (Imports)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    fan_out_imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    fan_out_imports.add(node.module.split('.')[0])
                    
            # Fan-In: Functions & Classes defined in this module
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                fan_in_definitions += 1

        fan_out = len(fan_out_imports)
        fan_in = max(1, fan_in_definitions)

        # 6. Assemble raw metrics dictionary
        raw_extracted_metrics = {
            'LOC': float(loc),
            'CYCLO': float(total_cyclo),
            'LENGTH': float(length),
            'VOLUME': float(volume),
            'DIFFICULTY': float(difficulty),
            'INT_FAN_IN': float(fan_in),
            'INT_FAN_OUT': float(fan_out),
            'NUM_OPERATORS': float(n1),
            'NUM_OPERANDS': float(n2),
            'BRANCH_COUNT': float(branch_count)
        }

        return {
            "filename": filename,
            "raw_metrics": raw_extracted_metrics,
            "most_suspicious_component": most_suspicious_component,
            "functions_analyzed": len(function_complexities),
            "function_breakdown": function_complexities,
            "external_dependencies": list(fan_out_imports)
        }

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Reads a Python file from disk and analyzes it.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            code_str = f.read()
            
        return self.analyze_source_code(code_str, filename=os.path.basename(file_path))

if __name__ == "__main__":
    # Test with sample Python code
    sample_code = '''
import os
import requests
import json

def process_payment(user_id, amount, is_vip, retry_count=3):
    """Processes user payment with multiple conditional discount and retry logic."""
    if amount <= 0:
        return {"status": "error", "msg": "Invalid amount"}
    
    final_amount = amount
    if is_vip:
        if amount > 1000:
            final_amount = amount * 0.85
        elif amount > 500:
            final_amount = amount * 0.90
        else:
            final_amount = amount * 0.95
            
    for attempt in range(retry_count):
        try:
            res = requests.post("https://payment.gateway.com/charge", json={"user": user_id, "amt": final_amount})
            if res.status_code == 200:
                return {"status": "success", "charge": final_amount}
        except Exception as e:
            if attempt == retry_count - 1:
                return {"status": "failed", "error": str(e)}
                
    return {"status": "timeout"}
'''
    analyzer = SourceCodeAnalyzer()
    analysis = analyzer.analyze_source_code(sample_code, "payment_service.py")
    
    print("\n" + "=" * 55)
    print("      SOURCE CODE STATIC METRICS EXTRACTION      ")
    print("=" * 55)
    print(f"Analyzed File:              {analysis['filename']}")
    print(f"Most Suspicious Component:  {analysis['most_suspicious_component']}")
    print(f"External Dependencies:      {analysis['external_dependencies']}")
    print("\nRaw Static Metrics Extracted:")
    for k, v in analysis['raw_metrics'].items():
        print(f"  - {k:<15}: {v}")

import os
import webbrowser
from database.functionsForDB import Database

# Module-level configuration
dbPath = os.getenv('DB_PATH', './shared/database/packages.db')
outputDir = os.path.dirname(dbPath)

def visualizePackageNeighborhood(package_type, package_name, depth=2, output_file=None, db_path=None):
    """
    Visualize the dependency neighborhood of a specific package
    """
    try:
        from pyvis.network import Network
    except ImportError:
        print("⚠️  Install pyvis: pip install pyvis")
        return None
    
    # Use provided db_path or fall back to module default
    db_path = db_path or dbPath
    db = Database(db_path)
    packageID = db.getPackageID(package_type, package_name)
    
    if not packageID:
        print(f"  ⚠️  Package {package_type}/{package_name} not found")
        db.close()
        return None
    
    # Get limited subgraph using recursive CTE
    query = """
    WITH RECURSIVE dep_tree AS (
        SELECT 
            p.PackageID,
            t.Type,
            n.Name,
            COALESCE(l.License, 'No License') as License,
            0 as Level,
            CAST(NULL AS INTEGER) as ParentID
        FROM Packages p
        JOIN Types t ON p.TypeID = t.TypeID
        JOIN Names n ON p.NameID = n.NameID
        LEFT JOIN Licenses l ON p.LicenseID = l.LicenseID
        WHERE p.PackageID = ?
        
        UNION ALL
        
        SELECT 
            p.PackageID,
            t.Type,
            n.Name,
            COALESCE(l.License, 'No License') as License,
            dt.Level + 1,
            dt.PackageID as ParentID
        FROM dep_tree dt
        JOIN Dependencies d ON dt.PackageID = d.DependsOnPackageID
        JOIN Packages p ON d.PackageID = p.PackageID
        JOIN Types t ON p.TypeID = t.TypeID
        JOIN Names n ON p.NameID = n.NameID
        LEFT JOIN Licenses l ON p.LicenseID = l.LicenseID
        WHERE dt.Level < ?
    )
    SELECT * FROM dep_tree
    """
    
    tree = db.con.execute(query, (packageID, depth)).fetchall()
    
    if len(tree) == 0:
        print(f"  ⚠️  No dependencies found")
        db.close()
        return None
    
    if len(tree) > 2000:
        print(f"  ⚠️  Subgraph too large ({len(tree)} nodes), reducing depth...")
        depth = 1
        tree = db.con.execute(query, (packageID, depth)).fetchall()
    
    print(f"  Extracted {len(tree)} nodes (depth {depth})")
    
    # Create visualization
    net = Network(height='900px', width='100%', directed=True, 
                 bgcolor='#1a1a2e', font_color='white')
    
    license_colors = {
        'MIT': '#00d4aa',
        'ISC': '#4169e1',
        'Apache-2.0': '#ff6b9d',
        'BSD-3-Clause': '#c5a3ff',
        'BSD-2-Clause': '#9b59b6',
        'GPL-3.0': '#e74c3c',
        'GPL-2.0': '#c0392b',
        'LGPL-3.0': '#f39c12',
        'No License': '#ff4757',
        'Unknown': '#95a5a6'
    }
    
    for row in tree:
        pkg_id, type, name, license, level, parent_id = row
        color = license_colors.get(license, license_colors['Unknown'])
        
        net.add_node(
            pkg_id, 
            label=name if len(name) < 30 else name[:27] + '...',
            color=color, 
            size=40 if level == 0 else 20,
            title=f"{name}\n{type}\n{license}\nLevel: {level}",
            shape='diamond' if level == 0 else 'dot'
        )
        
        if parent_id:
            net.add_edge(parent_id, pkg_id, color='#6c757d')
    
    net.set_options("""
    {
      "physics": {"enabled": false},
      "layout": {
        "hierarchical": {
          "enabled": true,
          "direction": "UD",
          "sortMethod": "directed"
        }
      }
    }
    """)
    
    # Generate output filename if not provided
    if not output_file:
        safe_name = package_name.replace('/', '_').replace('.', '_')
        output_dir = os.path.dirname(db_path)
        output_file = os.path.join(output_dir, f"neighborhood_{safe_name}.html")
    
    net.save_graph(output_file)
    print(f"  ✅ Saved: {output_file}")
    
    # Try to open in browser (works on host, shows path in Docker)
    try:
        webbrowser.open('file://' + os.path.abspath(output_file))
        print(f"  🌐 Opened in browser")
    except:
        host_path = output_file.replace('/app/shared', './shared')
        print(f"  📂 File available on host at: {host_path}")
    
    db.close()
    return output_file


class DependencyAnalytics:
    """
    Class for generating analytics and visualizations for large dependency graphs
    """
    def __init__(self, db_path=None):
        self.db_path = db_path or dbPath
        self.db = Database(self.db_path)
        self.output_dir = os.path.dirname(self.db_path)
    
    def getOverallStats(self):
        """
        Compute overall statistics about the dependency graph
        """
        stats = {}
        
        # Total packages
        stats['total_packages'] = self.db.con.execute(
            "SELECT COUNT(*) FROM Packages"
        ).fetchone()[0]
        
        # Total dependencies
        stats['total_dependencies'] = self.db.con.execute(
            "SELECT COUNT(*) FROM Dependencies"
        ).fetchone()[0]
        
        # License distribution
        stats['licenses'] = self.db.con.execute("""
            SELECT 
                COALESCE(l.License, 'No License') as License,
                COUNT(*) as Count
            FROM Packages p
            LEFT JOIN Licenses l ON p.LicenseID = l.LicenseID
            GROUP BY l.License
            ORDER BY Count DESC
            LIMIT 20
        """).fetchall()
        
        # Ecosystem distribution
        stats['ecosystems'] = self.db.con.execute("""
            SELECT 
                t.Type,
                COUNT(*) as Count
            FROM Packages p
            JOIN Types t ON p.TypeID = t.TypeID
            GROUP BY t.Type
            ORDER BY Count DESC
        """).fetchall()
        
        # Calculate dependency depth distribution using recursive CTE
        stats['depth_distribution'] = self.db.con.execute("""
            WITH RECURSIVE depth_calc AS (
                -- Base case: packages with no dependencies have depth 0
                SELECT 
                    p.PackageID,
                    0 as Depth
                FROM Packages p
                WHERE NOT EXISTS (
                    SELECT 1 FROM Dependencies d 
                    WHERE d.PackageID = p.PackageID
                )
                
                UNION ALL
                
                -- Recursive case: depth is 1 + max depth of dependencies
                SELECT 
                    d.PackageID,
                    dc.Depth + 1 as Depth
                FROM Dependencies d
                JOIN depth_calc dc ON d.DependsOnPackageID = dc.PackageID
            ),
            max_depths AS (
                SELECT PackageID, MAX(Depth) as MaxDepth
                FROM depth_calc
                GROUP BY PackageID
            )
            SELECT 
                MaxDepth as DepthLevel,
                COUNT(*) as Count
            FROM max_depths
            GROUP BY MaxDepth
            ORDER BY MaxDepth
            LIMIT 20
        """).fetchall()
        
        # Most depended-upon packages (top 50)
        stats['most_depended'] = self.db.con.execute("""
            SELECT 
                n.Name,
                t.Type,
                COUNT(*) as DependentCount
            FROM Dependencies d
            JOIN Packages p ON d.DependsOnPackageID = p.PackageID
            JOIN Names n ON p.NameID = n.NameID
            JOIN Types t ON p.TypeID = t.TypeID
            GROUP BY n.Name, t.Type
            ORDER BY DependentCount DESC
            LIMIT 50
        """).fetchall()
        
        # Packages with most dependencies
        stats['most_dependencies'] = self.db.con.execute("""
            SELECT 
                n.Name,
                t.Type,
                COUNT(*) as DependencyCount
            FROM Dependencies d
            JOIN Packages p ON d.PackageID = p.PackageID
            JOIN Names n ON p.NameID = n.NameID
            JOIN Types t ON p.TypeID = t.TypeID
            GROUP BY n.Name, t.Type
            ORDER BY DependencyCount DESC
            LIMIT 50
        """).fetchall()
        
        return stats
    
    def generateHTMLReport(self, output_file=None):
        """
        Generate a comprehensive HTML analytics report
        """
        # Default output file in the output directory
        if output_file is None:
            output_file = os.path.join(self.output_dir, "analytics_report.html")
        
        stats = self.getOverallStats()
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Dependency Analytics Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-2.26.0.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #0f0f1e;
            color: #e0e0e0;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            margin: 0;
            color: white;
            font-size: 2.5em;
        }}
        
        .header p {{
            margin: 10px 0 0 0;
            color: #f0f0f0;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: #1a1a2e;
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #667eea;
            text-align: center;
        }}
        
        .stat-card h3 {{
            margin: 0 0 10px 0;
            color: #667eea;
            font-size: 1.1em;
        }}
        
        .stat-card .value {{
            font-size: 2.5em;
            color: #00d4aa;
            font-weight: bold;
        }}
        
        .chart-container {{
            background: #1a1a2e;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            border: 2px solid #667eea;
        }}
        
        .chart-container h2 {{
            color: #667eea;
            margin-bottom: 15px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #333;
        }}
        
        th {{
            background: #667eea;
            color: white;
            font-weight: bold;
        }}
        
        tr:hover {{ background: #2a2a3e; }}
        
        .warning {{
            background: #ff4757;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Dependency Analytics Dashboard</h1>
        <p>Comprehensive analysis of {stats['total_packages']:,} packages and {stats['total_dependencies']:,} dependency relationships</p>
    </div>
    
    <div class="warning">
        ⚠️ <strong>Large Graph Notice:</strong> With {stats['total_packages']:,} nodes, traditional full-graph visualization is not possible. 
        This dashboard provides statistical analysis. Use the neighborhood visualizations for specific packages.
    </div>
    
    <div class="stats-grid">
        <div class="stat-card">
            <h3>Total Packages</h3>
            <div class="value">{stats['total_packages']:,}</div>
        </div>
        <div class="stat-card">
            <h3>Total Dependencies</h3>
            <div class="value">{stats['total_dependencies']:,}</div>
        </div>
        <div class="stat-card">
            <h3>Unique Licenses</h3>
            <div class="value">{len(stats['licenses'])}</div>
        </div>
        <div class="stat-card">
            <h3>Ecosystems</h3>
            <div class="value">{len(stats['ecosystems'])}</div>
        </div>
    </div>
    
    <div class="chart-container">
        <h2>📈 License Distribution (Top 20)</h2>
        <div id="license-chart"></div>
    </div>
    
    <div class="chart-container">
        <h2>🌳 Dependency Depth Distribution</h2>
        <div id="depth-chart"></div>
    </div>
    
    <div class="chart-container">
        <h2>📦 Ecosystem Distribution</h2>
        <div id="ecosystem-chart"></div>
    </div>
    
    <div class="chart-container">
        <h2>⭐ Top 50 Most Depended-Upon Packages</h2>
        <p style="margin-bottom:10px; color:#a8a8ff;">These packages are critical to the ecosystem</p>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Package</th>
                    <th>Type</th>
                    <th>Dependents</th>
                </tr>
            </thead>
            <tbody>
                {''.join(f'<tr><td>{i+1}</td><td>{name}</td><td>{type}</td><td>{count:,}</td></tr>' 
                        for i, (name, type, count) in enumerate(stats['most_depended']))}
            </tbody>
        </table>
    </div>
    
    <div class="chart-container">
        <h2>🔗 Packages with Most Dependencies</h2>
        <p style="margin-bottom:10px; color:#a8a8ff;">These packages have the most complex dependency trees</p>
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th>Package</th>
                    <th>Type</th>
                    <th>Dependencies</th>
                </tr>
            </thead>
            <tbody>
                {''.join(f'<tr><td>{i+1}</td><td>{name}</td><td>{type}</td><td>{count:,}</td></tr>' 
                        for i, (name, type, count) in enumerate(stats['most_dependencies']))}
            </tbody>
        </table>
    </div>
    
    <script>
        // License distribution chart
        const licenseData = {{
            x: {[lic for lic, _ in stats['licenses']]},
            y: {[count for _, count in stats['licenses']]},
            type: 'bar',
            marker: {{ color: '#00d4aa' }}
        }};
        
        Plotly.newPlot('license-chart', [licenseData], {{
            plot_bgcolor: '#0f0f1e',
            paper_bgcolor: '#1a1a2e',
            font: {{color: 'white'}},
            margin: {{l: 50, r: 20, t: 20, b: 100}},
            xaxis: {{tickangle: -45}}
        }});
        
        // Depth distribution chart
        const depthData = {{
            x: {[level for level, _ in stats['depth_distribution']]},
            y: {[count for _, count in stats['depth_distribution']]},
            type: 'scatter',
            mode: 'lines+markers',
            line: {{color: '#667eea', width: 3}},
            marker: {{size: 8}}
        }};
        
        Plotly.newPlot('depth-chart', [depthData], {{
            plot_bgcolor: '#0f0f1e',
            paper_bgcolor: '#1a1a2e',
            font: {{color: 'white'}},
            margin: {{l: 50, r: 20, t: 20, b: 50}},
            xaxis: {{title: 'Dependency Depth Level'}},
            yaxis: {{title: 'Number of Packages', type: 'log'}}
        }});
        
        // Ecosystem distribution chart
        const ecosystemData = {{
            labels: {[eco for eco, _ in stats['ecosystems']]},
            values: {[count for _, count in stats['ecosystems']]},
            type: 'pie',
            marker: {{
                colors: ['#00d4aa', '#4169e1', '#ff6b9d', '#c5a3ff', '#ffa500', '#ff4757']
            }}
        }};
        
        Plotly.newPlot('ecosystem-chart', [ecosystemData], {{
            plot_bgcolor: '#0f0f1e',
            paper_bgcolor: '#1a1a2e',
            font: {{color: 'white'}},
            margin: {{l: 50, r: 20, t: 20, b: 50}}
        }});
    </script>
</body>
</html>
"""
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ Analytics report generated: {output_file}")
        
        # Try to open in browser (works on host, shows path in Docker)
        try:
            webbrowser.open('file://' + os.path.abspath(output_file))
            print(f"🌐 Opened in browser")
        except:
            host_path = output_file.replace('/app/shared', './shared')
            print(f"📂 File available on host at: {host_path}")
        
        return output_file
    
    def close(self):
        """Close database connection"""
        self.db.close()


# Example usage
if __name__ == "__main__":
    print("🎨 Dependency Visualization Toolkit\n")
    
    # Generate analytics report
    analytics = DependencyAnalytics()
    analytics.generateHTMLReport()
    analytics.close()
    
    # Example: Visualize a specific package neighborhood
    # visualizePackageNeighborhood('npm', 'express', depth=2)
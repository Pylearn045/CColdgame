// Unity editor window to import map JSON and preview layers (skeleton)
// Place under Assets/Editor in a Unity project and open via Window -> Map Importer

using System.IO;
using UnityEngine;
using UnityEditor;
using Newtonsoft.Json;

public class MapImporterWindow : EditorWindow {
    string jsonPath = "map_96x96.json";
    int tileSize = 32;
    MapData map;
    Vector2 scroll;

    [MenuItem("Window/Map Importer")]
    public static void ShowWindow() {
        GetWindow<MapImporterWindow>("Map Importer");
    }

    void OnGUI() {
        GUILayout.Label("Map Importer", EditorStyles.boldLabel);
        jsonPath = EditorGUILayout.TextField("JSON Path (relative to project root)", jsonPath);
        tileSize = EditorGUILayout.IntField("Tile Size", tileSize);
        if (GUILayout.Button("Load JSON")) {
            LoadJson();
        }

        if (map != null) {
            GUILayout.Label($"Map: {map.width}x{map.height}");
            if (GUILayout.Button("Generate Preview GameObjects")) {
                GeneratePreview();
            }
        }
    }

    void LoadJson() {
        var full = Path.Combine(Application.dataPath, "..", jsonPath);
        if (!File.Exists(full)) { Debug.LogError("Map JSON not found: " + full); return; }
        var txt = File.ReadAllText(full);
        map = JsonConvert.DeserializeObject<MapData>(txt);
        Debug.Log("Loaded map: " + map.width + "x" + map.height);
    }

    void GeneratePreview() {
        if (map == null) return;
        var root = new GameObject("MapPreview");

            // Load textures from Unity project Assets
            Texture2D texPlain = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Tiles/plain.png");
            Texture2D texMountain = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Tiles/mountain.png");
            Texture2D texForest = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Tiles/forest.png");
            Texture2D texDeepForest = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Tiles/deep_forest.png");
            Texture2D texLake = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Tiles/lake.png");

            Material baseMat = new Material(Shader.Find("Unlit/Transparent"));

            int levels = (map.levels > 0) ? map.levels : 1;

            for (int r = 0; r < map.height; r++) {
                for (int c = 0; c < map.width; c++) {
                    int t = map.tiles[r][c];

                    // Decide base texture: water -> lake; else use height levels for mountain/plain; sprinkle forest deterministically
                    Texture2D baseTex = texPlain;
                    bool isForest = false;
                    if (t == 2) {
                        baseTex = texLake;
                    } else if (map.height_levels != null) {
                        int lvl = map.height_levels[r][c];
                        if (lvl >= levels - 1) baseTex = texMountain;
                        else {
                            // deterministic pseudo-random for forest distribution
                            int hash = (r * 73856093) ^ (c * 19349663);
                            int val = Mathf.Abs(hash) % 100;
                            if (val < 8) { isForest = true; baseTex = texDeepForest; }
                            else if (val < 22) { isForest = true; baseTex = texForest; }
                            else baseTex = texPlain;
                        }
                    }

                    var go = GameObject.CreatePrimitive(PrimitiveType.Quad);
                    go.transform.parent = root.transform;
                    float worldScale = tileSize / 100.0f;
                    go.transform.position = new Vector3(c * worldScale, 0, r * worldScale);
                    go.transform.localScale = new Vector3(worldScale, worldScale, 1);
                    go.name = $"Tile_{r}_{c}_T{t}";

                    var mr = go.GetComponent<MeshRenderer>();
                    var mat = new Material(baseMat) { mainTexture = baseTex };
                    mr.sharedMaterial = mat;

                    // Simple transition overlay: if neighbor has different base, place a semi-transparent overlay to hint transition
                    (int dx, int dy, string dir)[] nbrs = new (int, int, string)[] {
                        (0, -1, "n"), (0, 1, "s"), (1, 0, "e"), (-1, 0, "w")
                    };
                    foreach (var nb in nbrs) {
                        int nx = c + nb.dx;
                        int ny = r + nb.dy;
                        if (nx < 0 || nx >= map.width || ny < 0 || ny >= map.height) continue;
                        Texture2D nbTex = texPlain;
                        int nt = map.tiles[ny][nx];
                        if (nt == 2) nbTex = texLake;
                        else if (map.height_levels != null) {
                            int nl = map.height_levels[ny][nx];
                            if (nl >= levels - 1) nbTex = texMountain;
                            else {
                                int hash2 = (ny * 73856093) ^ (nx * 19349663);
                                int vv = Mathf.Abs(hash2) % 100;
                                if (vv < 8) nbTex = texDeepForest;
                                else if (vv < 22) nbTex = texForest;
                                else nbTex = texPlain;
                            }
                        }
                        if (nbTex != baseTex) {
                            var ov = GameObject.CreatePrimitive(PrimitiveType.Quad);
                            ov.transform.parent = root.transform;
                            // Slightly above so it renders on top
                            ov.transform.position = new Vector3(c * worldScale, 0.01f, r * worldScale);
                            ov.transform.localScale = new Vector3(worldScale, worldScale, 1);
                            ov.name = $"Overlay_{r}_{c}_{nb.dir}";
                            var mr2 = ov.GetComponent<MeshRenderer>();
                            var mat2 = new Material(baseMat) { mainTexture = nbTex, color = new Color(1,1,1,0.45f) };
                            mr2.sharedMaterial = mat2;
                        }
                    }
                }
            }

            Debug.Log("Map preview generated under GameObject 'MapPreview'.");
        }
}

// Data container must match JSON shape
public class MapData {
    public int width; public int height; public int[][] tiles; public int[][] layers; public object tile_enum;
}

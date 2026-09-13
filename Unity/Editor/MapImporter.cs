// Unity editor window to import map JSON, preview and edit tiles in-scene.
// Place under Assets/Editor in a Unity project and open via Window -> Map Importer

using System.IO;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;
using Newtonsoft.Json;

public class MapImporterWindow : EditorWindow {
    string jsonPath = "map_96x96_L4.json";
    int tileSize = 32;
    MapData map;
    Vector2 scroll;

    // textures
    Texture2D texPlain, texMountain, texForest, texDeepForest, texLake;

    // editing state
    bool editMode = false;
    int selectedTerrain = 0; // 0=plain,1=mountain,2=forest,3=deep_forest,4=lake
    string[] terrainNames = new string[] {"Plain","Mountain","Forest","DeepForest","Lake"};
    int brushSize = 1;

    // Undo stack for visual map
    Stack<int[,]> undoStack = new Stack<int[,]>();

    [MenuItem("Window/Map Importer")]
    public static void ShowWindow() {
        GetWindow<MapImporterWindow>("Map Importer");
    }

    void OnEnable() {
        SceneView.duringSceneGui += OnSceneGUI;
    }
    void OnDisable() {
        SceneView.duringSceneGui -= OnSceneGUI;
    }

    void OnGUI() {
        GUILayout.Label("Map Importer & Editor", EditorStyles.boldLabel);
        jsonPath = EditorGUILayout.TextField("JSON Path (relative to project root)", jsonPath);
        tileSize = EditorGUILayout.IntField("Tile Size (px)", tileSize);

        EditorGUILayout.Space();
        if (GUILayout.Button("Load JSON")) {
            LoadJson();
        }

        if (map != null) {
            GUILayout.Label($"Map: {map.width} x {map.height}");
            if (GUILayout.Button("Generate Preview GameObjects")) {
                GeneratePreview();
            }

            EditorGUILayout.Space();
            editMode = EditorGUILayout.Toggle("Edit Mode (Scene)", editMode);
            selectedTerrain = GUILayout.Toolbar(selectedTerrain, terrainNames);
            brushSize = EditorGUILayout.IntSlider("Brush Size", brushSize, 1, 5);

            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Undo")) DoUndo();
            if (GUILayout.Button("Save JSON (S)")) SaveJson();
            GUILayout.EndHorizontal();

            EditorGUILayout.HelpBox("In Scene View: Left click = paint, Right click = erase (to Plain). Press S in editor window to save.", MessageType.Info);
        }

        if (GUILayout.Button("Refresh textures from Assets/Tiles")) LoadTextures();
    }

    void LoadTextures() {
        texPlain = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Tiles/plain.png");
        texMountain = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Tiles/mountain.png");
        texForest = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Tiles/forest.png");
        texDeepForest = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Tiles/deep_forest.png");
        texLake = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Tiles/lake.png");
    }

    void LoadJson() {
        var full = Path.Combine(Application.dataPath, "..", jsonPath);
        if (!File.Exists(full)) { Debug.LogError("Map JSON not found: " + full); return; }
        var txt = File.ReadAllText(full);
        map = JsonConvert.DeserializeObject<MapData>(txt);

        // ensure visual layer exists
        if (map.visual == null) {
            map.visual = new int[map.height][];
            for (int r = 0; r < map.height; r++) {
                map.visual[r] = new int[map.width];
                for (int c = 0; c < map.width; c++) map.visual[r][c] = -1; // -1 = unset
            }
        }

        LoadTextures();
        Debug.Log("Loaded map: " + map.width + "x" + map.height);
    }

    GameObject previewRoot = null;

    void ClearPreview() {
        if (previewRoot != null) {
            DestroyImmediate(previewRoot);
            previewRoot = null;
        }
    }

    void GeneratePreview() {
        if (map == null) return;
        ClearPreview();
        previewRoot = new GameObject("MapPreview");

        int levels = (map.levels > 0) ? map.levels : 1;

        for (int r = 0; r < map.height; r++) {
            for (int c = 0; c < map.width; c++) {
                Texture2D baseTex = DecideTextureForCell(r, c, levels);
                var go = GameObject.CreatePrimitive(PrimitiveType.Quad);
                go.transform.parent = previewRoot.transform;
                float worldScale = tileSize / 100.0f;
                go.transform.position = new Vector3(c * worldScale, 0, r * worldScale);
                go.transform.localScale = new Vector3(worldScale, worldScale, 1);
                go.name = $"Tile_{r}_{c}";

                var mr = go.GetComponent<MeshRenderer>();
                var mat = new Material(Shader.Find("Unlit/Texture")) { mainTexture = baseTex };
                mr.sharedMaterial = mat;

                // ensure colliders exist for scene picking
                var col = go.GetComponent<Collider>();
                if (col == null) go.AddComponent<BoxCollider>();
            }
        }

        Debug.Log("Map preview generated under GameObject 'MapPreview'.");
    }

    Texture2D DecideTextureForCell(int r, int c, int levels) {
        // If a visual override exists, use it
        if (map.visual != null && map.visual[r][c] >= 0) {
            switch (map.visual[r][c]) {
                case 0: return texPlain;
                case 1: return texMountain;
                case 2: return texForest;
                case 3: return texDeepForest;
                case 4: return texLake;
            }
        }

        // fallback to previous heuristic
        int t = map.tiles[r][c];
        if (t == 2) return texLake;
        if (map.height_levels != null) {
            int lvl = map.height_levels[r][c];
            if (lvl >= levels - 1) return texMountain;
            int hash = (r * 73856093) ^ (c * 19349663);
            int val = Mathf.Abs(hash) % 100;
            if (val < 8) return texDeepForest;
            if (val < 22) return texForest;
            return texPlain;
        }
        return texPlain;
    }

    void OnSceneGUI(SceneView sv) {
        if (!editMode || map == null || previewRoot == null) return;

        Event e = Event.current;
        if ((e.type == EventType.MouseDown) && (e.button == 0 || e.button == 1)) {
            Ray ray = HandleUtility.GUIPointToWorldRay(e.mousePosition);
            if (Physics.Raycast(ray, out RaycastHit hit, 1000f)) {
                var go = hit.collider.gameObject;
                if (go.name.StartsWith("Tile_")) {
                    // parse row,col from name
                    var parts = go.name.Split('_');
                    if (parts.Length >= 3) {
                        int r = int.Parse(parts[1]);
                        int c = int.Parse(parts[2]);
                        // push undo snapshot
                        PushUndoSnapshot();
                        if (e.button == 0) PaintAt(r, c, selectedTerrain);
                        else if (e.button == 1) PaintAt(r, c, 0); // right click -> plain
                        e.Use();
                        SceneView.RepaintAll();
                    }
                }
            }
        }

        // Keyboard shortcut: S to save (when window focused)
        if (e.type == EventType.KeyDown && e.keyCode == KeyCode.S) {
            SaveJson();
            e.Use();
        }
    }

    void PushUndoSnapshot() {
        if (map.visual == null) return;
        int h = map.height; int w = map.width;
        int[,] snap = new int[h,w];
        for (int r = 0; r < h; r++) for (int c = 0; c < w; c++) snap[r,c] = map.visual[r][c];
        undoStack.Push(snap);
        // limit
        if (undoStack.Count > 50) undoStack.TrimExcess();
    }

    void DoUndo() {
        if (undoStack.Count == 0) return;
        var snap = undoStack.Pop();
        int h = map.height; int w = map.width;
        for (int r = 0; r < h; r++) for (int c = 0; c < w; c++) map.visual[r][c] = snap[r,c];
        // refresh preview materials
        UpdatePreviewMaterials();
    }

    void PaintAt(int r, int c, int terrainIndex) {
        int h = map.height; int w = map.width;
        int half = brushSize / 2;
        for (int oy = -half; oy <= half; oy++) {
            for (int ox = -half; ox <= half; ox++) {
                int ny = r + oy; int nx = c + ox;
                if (ny < 0 || ny >= h || nx < 0 || nx >= w) continue;
                map.visual[ny][nx] = terrainIndex;
                UpdateTileMaterial(ny, nx, terrainIndex);
            }
        }
    }

    void UpdateTileMaterial(int r, int c, int terrainIndex) {
        if (previewRoot == null) return;
        var go = previewRoot.transform.Find($"Tile_{r}_{c}");
        if (go == null) return;
        var mr = go.GetComponent<MeshRenderer>();
        if (mr == null) return;
        Texture2D tex = texPlain;
        switch (terrainIndex) {
            case 0: tex = texPlain; break;
            case 1: tex = texMountain; break;
            case 2: tex = texForest; break;
            case 3: tex = texDeepForest; break;
            case 4: tex = texLake; break;
        }
        mr.sharedMaterial.mainTexture = tex;
        // mark scene dirty
        EditorUtility.SetDirty(mr);
    }

    void UpdatePreviewMaterials() {
        if (previewRoot == null) return;
        int h = map.height; int w = map.width;
        for (int r = 0; r < h; r++) {
            for (int c = 0; c < w; c++) {
                int idx = (map.visual != null) ? map.visual[r][c] : -1;
                if (idx >= 0) UpdateTileMaterial(r, c, idx);
            }
        }
    }

    void SaveJson() {
        if (map == null) return;
        var full = Path.Combine(Application.dataPath, "..", jsonPath);
        var txt = JsonConvert.SerializeObject(map, Formatting.Indented);
        File.WriteAllText(full, txt);
        AssetDatabase.Refresh();
        Debug.Log("Saved map JSON: " + full);
    }
}

// Data container must match JSON shape
public class MapData {
    public int width; public int height; public int[][] tiles; public int[][] layers; public object tile_enum;
    public int levels; public int[][] height_levels; public int[][][] layers_list; // original shape compatibility
    // visual overlay for editor (0=plain,1=mountain,2=forest,3=deep_forest,4=lake)
    public int[][] visual;
}

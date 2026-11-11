// Extractor de dependencias entre tipos de un servicio .NET de QUICKPATCH (SCRUM-681).
//
// Lee los ensamblados compilados QuickPatch.<Servicio>.{Api,Application,Domain,Infrastructure}.dll
// y su PDB portable, y escribe un JSON con los tipos (capa, paquete, archivo y líneas) y las
// dependencias entre tipos. Las dependencias salen del binario: herencia, interfaces, campos,
// firmas de métodos, variables locales y cada tipo, método o campo que el IL referencia.
// Los tipos generados por el compilador (closures, máquinas de estado async) se atribuyen al
// tipo que los declara. Solo usa System.Reflection.Metadata (incluido en el runtime).
//
// Uso: extractor-dotnet <carpeta-bin> <Servicio> <salida.json>

using System.Collections.Immutable;
using System.Reflection;
using System.Reflection.Emit;
using System.Reflection.Metadata;
using System.Reflection.Metadata.Ecma335;
using System.Reflection.PortableExecutable;
using System.Text.Json;

if (args.Length != 3)
{
    Console.Error.WriteLine("Uso: extractor-dotnet <carpeta-bin> <Servicio> <salida.json>");
    return 2;
}

var (binDir, servicio, salida) = (args[0], args[1], args[2]);
string[] capas = ["Api", "Application", "Domain", "Infrastructure"];
var tipos = new Dictionary<string, TipoInfo>(StringComparer.Ordinal);
var deps = new HashSet<(string De, string A)>();
var externas = new HashSet<(string De, string Ns)>();

foreach (var capa in capas)
{
    var dll = Path.Combine(binDir, $"QuickPatch.{servicio}.{capa}.dll");
    if (!File.Exists(dll))
    {
        Console.Error.WriteLine($"No existe {dll}");
        return 1;
    }
    Extraer(dll, capa);
}

var json = new
{
    servicio,
    lenguaje = "csharp",
    tipos = tipos.Values.OrderBy(t => t.Id).ToList(),
    dependencias = deps.Where(d => d.De != d.A && tipos.ContainsKey(d.A))
        .OrderBy(d => d.De).ThenBy(d => d.A).Select(d => new { de = d.De, a = d.A }),
    externas = externas.OrderBy(d => d.De).ThenBy(d => d.Ns).Select(d => new { de = d.De, ns = d.Ns }),
};
Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(salida))!);
File.WriteAllText(salida, JsonSerializer.Serialize(json, new JsonSerializerOptions { WriteIndented = true }));
Console.WriteLine($"{servicio}: {tipos.Count} tipos, {deps.Count} dependencias internas -> {salida}");
return 0;

void Extraer(string dll, string capa)
{
    using var fs = File.OpenRead(dll);
    using var pe = new PEReader(fs);
    var md = pe.GetMetadataReader();
    MetadataReader? pdb = null;
    MetadataReaderProvider? pdbProvider = null;
    var pdbPath = Path.ChangeExtension(dll, ".pdb");
    if (File.Exists(pdbPath))
    {
        pdbProvider = MetadataReaderProvider.FromPortablePdbStream(File.OpenRead(pdbPath));
        pdb = pdbProvider.GetMetadataReader();
    }

    var nombres = new NombreTipos(md);
    foreach (var h in md.TypeDefinitions)
    {
        var td = md.GetTypeDefinition(h);
        var id = nombres.Definicion(h);
        if (!EsPropio(id)) continue;

        if (!tipos.TryGetValue(id, out var info))
        {
            var raiz = md.GetTypeDefinition(nombres.Raiz(h));
            info = new TipoInfo(id, Paquete(id), capa, Clase(md, raiz));
            tipos[id] = info;
        }

        void Usa(IEnumerable<string> ns)
        {
            foreach (var n in ns)
            {
                if (EsPropio(n)) deps.Add((id, n));
                else if (n.Length > 0 && n[0] != '<' && !n.StartsWith("System.", StringComparison.Ordinal) && n != "System")
                    externas.Add((id, Externo(n)));
            }
        }

        if (!td.BaseType.IsNil) Usa(nombres.DeHandle(td.BaseType));
        foreach (var ih in td.GetInterfaceImplementations())
            Usa(nombres.DeHandle(md.GetInterfaceImplementation(ih).Interface));
        foreach (var fh in td.GetFields())
            Usa(Partes(md.GetFieldDefinition(fh).DecodeSignature(nombres, null)));

        foreach (var mh in td.GetMethods())
        {
            var m = md.GetMethodDefinition(mh);
            var sig = m.DecodeSignature(nombres, null);
            Usa(Partes(sig.ReturnType));
            foreach (var p in sig.ParameterTypes) Usa(Partes(p));
            if (m.RelativeVirtualAddress == 0) continue;
            var body = pe.GetMethodBody(m.RelativeVirtualAddress);
            if (!body.LocalSignature.IsNil)
            {
                var locales = md.GetStandaloneSignature(body.LocalSignature).DecodeLocalSignature(nombres, null);
                foreach (var l in locales) Usa(Partes(l));
            }
            foreach (var token in Il.Tokens(body.GetILReader()))
                Usa(nombres.DeToken(token));

            if (pdb is not null) info.AgregarLineas(pdb, mh);
        }
    }
    pdbProvider?.Dispose();
}

static bool EsPropio(string n) => n.StartsWith("QuickPatch.", StringComparison.Ordinal) || n == "Program";

static string Externo(string n)
{
    // Espacio de nombres sin el tipo, reducido a dos segmentos: Microsoft.EntityFrameworkCore, Confluent.Kafka, Npgsql.
    var p = n.Split('.');
    var ns = p.Length > 1 ? p[..^1] : p;
    return string.Join('.', ns.Take(2));
}

static string Paquete(string id)
{
    var i = id.LastIndexOf('.');
    return i < 0 ? "(global)" : id[..i];
}

static string Clase(MetadataReader md, TypeDefinition td)
{
    var a = td.Attributes;
    if ((a & TypeAttributes.Interface) != 0) return "interface";
    if (!td.BaseType.IsNil)
    {
        var b = NombreTipos.NombreSimple(md, td.BaseType);
        if (b == "System.Enum") return "enum";
        if (b == "System.ValueType") return "struct";
    }
    if ((a & TypeAttributes.Abstract) != 0 && (a & TypeAttributes.Sealed) != 0) return "static";
    if ((a & TypeAttributes.Abstract) != 0) return "abstract";
    return "class";
}

static IEnumerable<string> Partes(string s) => s.Split('|', StringSplitOptions.RemoveEmptyEntries);

sealed class TipoInfo(string id, string paquete, string capa, string clase)
{
    public string Id { get; } = id;
    public string Paquete { get; } = paquete;
    public string Capa { get; } = capa;
    public string Clase { get; } = clase;
    public string? Archivo { get; private set; }
    public int Lineas => _min == int.MaxValue ? 0 : _max - _min + 1;
    int _min = int.MaxValue, _max;

    public void AgregarLineas(MetadataReader pdb, MethodDefinitionHandle mh)
    {
        var info = pdb.GetMethodDebugInformation(mh);
        foreach (var sp in info.GetSequencePoints())
        {
            if (sp.IsHidden) continue;
            var doc = pdb.GetString(pdb.GetDocument(sp.Document).Name);
            Archivo ??= doc;
            if (doc != Archivo) continue;
            _min = Math.Min(_min, sp.StartLine);
            _max = Math.Max(_max, sp.EndLine);
        }
    }
}

/// Nombres de tipo como "Namespace.Tipo"; los anidados se reducen al tipo raíz.
/// Como proveedor de firmas, devuelve los nombres que aparecen separados por '|'.
sealed class NombreTipos(MetadataReader md) : ISignatureTypeProvider<string, object?>
{
    public TypeDefinitionHandle Raiz(TypeDefinitionHandle h)
    {
        var td = md.GetTypeDefinition(h);
        while (td.IsNested) { h = td.GetDeclaringType(); td = md.GetTypeDefinition(h); }
        return h;
    }

    public string Definicion(TypeDefinitionHandle h)
    {
        var td = md.GetTypeDefinition(Raiz(h));
        var ns = md.GetString(td.Namespace);
        var n = Limpio(md.GetString(td.Name));
        return ns.Length == 0 ? n : $"{ns}.{n}";
    }

    public string Referencia(TypeReferenceHandle h)
    {
        var tr = md.GetTypeReference(h);
        while (tr.ResolutionScope.Kind == HandleKind.TypeReference)
            tr = md.GetTypeReference((TypeReferenceHandle)tr.ResolutionScope);
        var ns = md.GetString(tr.Namespace);
        var n = Limpio(md.GetString(tr.Name));
        return ns.Length == 0 ? n : $"{ns}.{n}";
    }

    public static string NombreSimple(MetadataReader md, EntityHandle h) => h.Kind switch
    {
        HandleKind.TypeReference => new NombreTipos(md).Referencia((TypeReferenceHandle)h),
        HandleKind.TypeDefinition => new NombreTipos(md).Definicion((TypeDefinitionHandle)h),
        _ => "",
    };

    public IEnumerable<string> DeHandle(EntityHandle h) => h.Kind switch
    {
        HandleKind.TypeDefinition => [Definicion((TypeDefinitionHandle)h)],
        HandleKind.TypeReference => [Referencia((TypeReferenceHandle)h)],
        HandleKind.TypeSpecification => md.GetTypeSpecification((TypeSpecificationHandle)h).DecodeSignature(this, null)
            .Split('|', StringSplitOptions.RemoveEmptyEntries),
        _ => [],
    };

    public IEnumerable<string> DeToken(int token)
    {
        var h = MetadataTokens.EntityHandle(token);
        switch (h.Kind)
        {
            case HandleKind.TypeDefinition:
            case HandleKind.TypeReference:
            case HandleKind.TypeSpecification:
                return DeHandle(h);
            case HandleKind.MethodDefinition:
                return [Definicion(md.GetMethodDefinition((MethodDefinitionHandle)h).GetDeclaringType())];
            case HandleKind.FieldDefinition:
                return [Definicion(md.GetFieldDefinition((FieldDefinitionHandle)h).GetDeclaringType())];
            case HandleKind.MemberReference:
                var mr = md.GetMemberReference((MemberReferenceHandle)h);
                return mr.Parent.Kind is HandleKind.TypeReference or HandleKind.TypeDefinition or HandleKind.TypeSpecification
                    ? DeHandle(mr.Parent) : [];
            case HandleKind.MethodSpecification:
                var ms = md.GetMethodSpecification((MethodSpecificationHandle)h);
                var args = ms.DecodeSignature(this, null).SelectMany(a => a.Split('|', StringSplitOptions.RemoveEmptyEntries));
                return DeToken(MetadataTokens.GetToken(ms.Method)).Concat(args);
            default:
                return [];
        }
    }

    static string Limpio(string n)
    {
        var i = n.IndexOf('`');
        return i < 0 ? n : n[..i];
    }

    public string GetPrimitiveType(PrimitiveTypeCode typeCode) => "";
    public string GetTypeFromDefinition(MetadataReader r, TypeDefinitionHandle h, byte k) => Definicion(h);
    public string GetTypeFromReference(MetadataReader r, TypeReferenceHandle h, byte k) => Referencia(h);
    public string GetTypeFromSpecification(MetadataReader r, object? c, TypeSpecificationHandle h, byte k) =>
        r.GetTypeSpecification(h).DecodeSignature(this, c);
    public string GetSZArrayType(string e) => e;
    public string GetArrayType(string e, ArrayShape s) => e;
    public string GetByReferenceType(string e) => e;
    public string GetPointerType(string e) => e;
    public string GetPinnedType(string e) => e;
    public string GetGenericInstantiation(string g, ImmutableArray<string> a) => string.Join('|', a.Prepend(g));
    public string GetGenericMethodParameter(object? c, int i) => "";
    public string GetGenericTypeParameter(object? c, int i) => "";
    public string GetFunctionPointerType(MethodSignature<string> s) => "";
    public string GetModifiedType(string m, string u, bool r) => u;
}

/// Recorre el IL y devuelve los tokens de metadatos que referencian tipos, métodos o campos.
static class Il
{
    static readonly Dictionary<short, OperandType> Operandos = typeof(OpCodes)
        .GetFields(BindingFlags.Public | BindingFlags.Static)
        .Select(f => (OpCode)f.GetValue(null)!)
        .ToDictionary(o => o.Value, o => o.OperandType);

    public static IEnumerable<int> Tokens(BlobReader il)
    {
        var lista = new List<int>();
        while (il.RemainingBytes > 0)
        {
            short valor = il.ReadByte();
            if (valor == 0xFE) valor = unchecked((short)(0xFE00 | il.ReadByte()));
            if (!Operandos.TryGetValue(valor, out var op)) break;
            switch (op)
            {
                case OperandType.InlineType:
                case OperandType.InlineMethod:
                case OperandType.InlineField:
                case OperandType.InlineTok:
                    lista.Add(il.ReadInt32());
                    break;
                case OperandType.InlineNone: break;
                case OperandType.ShortInlineBrTarget:
                case OperandType.ShortInlineI:
                case OperandType.ShortInlineVar: il.ReadByte(); break;
                case OperandType.InlineVar: il.ReadInt16(); break;
                case OperandType.InlineI8:
                case OperandType.InlineR: il.ReadInt64(); break;
                case OperandType.InlineSwitch:
                    var n = il.ReadInt32();
                    for (var i = 0; i < n; i++) il.ReadInt32();
                    break;
                default: il.ReadInt32(); break; // InlineBrTarget, InlineI, InlineSig, InlineString, ShortInlineR(4)
            }
        }
        return lista;
    }
}

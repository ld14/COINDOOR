import { useState } from 'react';
import { ChoiceCards, Dropzone, InlineSuggestion, ListEditor, NumberStepper, SegmentedControl, itemsALineas } from '@/components/dos/entrada';

const tratamientos = [
  { value: 'completo', label: 'Completo' },
  { value: 'basico', label: 'Básico' },
  { value: 'sin-video', label: 'Sin video', disabled: true },
];

const formatos = [
  { value: 'arcade', label: 'Arcade', subtitle: 'ROM de MAME' },
  { value: 'consola', label: 'Consola', subtitle: 'Cartucho o disco', recommended: 'ArcadeDB' },
  { value: 'pc', label: 'PC', subtitle: 'Ejecutable', disabled: true },
];

export function EntradaDemo() {
  const [tratamiento, setTratamiento] = useState('completo');
  const [formato, setFormato] = useState('consola');
  const [jugadores, setJugadores] = useState(2);
  const [pasos, setPasos] = useState(['Insertá una moneda', 'Presioná Start']);
  const [archivo, setArchivo] = useState('');
  const [progreso, setProgreso] = useState<number | undefined>(40);
  const [sugerencia, setSugerencia] = useState(true);
  const [valorTitulo, setValorTitulo] = useState('');

  return (
    <section aria-label="Primitivas de entrada" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
      <h2>Entrada</h2>

      <div>
        <h3>SegmentedControl</h3>
        <SegmentedControl ariaLabel="Tratamiento" onChange={setTratamiento} options={tratamientos} value={tratamiento} />
        <p>Deshabilitado entero:</p>
        <SegmentedControl ariaLabel="Tratamiento (bloqueado)" disabled onChange={setTratamiento} options={tratamientos} value="basico" />
      </div>

      <div>
        <h3>ChoiceCards</h3>
        <ChoiceCards ariaLabel="Formato" onChange={setFormato} options={formatos} value={formato} />
        <p>Sin selección, con recomendada:</p>
        <ChoiceCards ariaLabel="Formato sin selección" onChange={setFormato} options={formatos} value="" />
      </div>

      <div>
        <h3>NumberStepper</h3>
        <NumberStepper ariaLabel="Jugadores" max={4} min={1} onChange={setJugadores} value={jugadores} />
        <p>En el mínimo, en el máximo y deshabilitado:</p>
        <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
          <NumberStepper ariaLabel="Jugadores (mínimo)" max={4} min={1} onChange={() => undefined} value={1} />
          <NumberStepper ariaLabel="Jugadores (máximo)" max={4} min={1} onChange={() => undefined} value={4} />
          <NumberStepper ariaLabel="Jugadores (bloqueado)" disabled max={4} min={1} onChange={() => undefined} value={2} />
        </div>
      </div>

      <div>
        <h3>ListEditor</h3>
        <ListEditor ariaLabel="Primeros pasos" items={pasos} onChange={setPasos} />
        <pre>{itemsALineas(pasos)}</pre>
        <p>Vacío y deshabilitado:</p>
        <ListEditor ariaLabel="Reglas (vacío)" itemLabel="Regla" items={[]} onChange={() => undefined} />
        <ListEditor ariaLabel="Reglas (bloqueado)" disabled items={['Regla fija']} itemLabel="Regla" onChange={() => undefined} />
      </div>

      <div>
        <h3>Dropzone</h3>
        <Dropzone accept="image/*" onFile={(file) => setArchivo(file.name)} secondaryAction={{ label: 'Buscar en ArcadeDB', onClick: () => undefined }} />
        <p>{archivo ? `Recibido: ${archivo}` : 'Nada recibido todavía.'}</p>
        <p>Subiendo:</p>
        <Dropzone onCancel={() => setProgreso(undefined)} onFile={() => undefined} progress={progreso ?? 0} />
        <p>Deshabilitada:</p>
        <Dropzone accept="image/*" disabled onFile={() => undefined} />
      </div>

      <div>
        <h3>InlineSuggestion</h3>
        <input aria-label="Título" onChange={(event) => setValorTitulo(event.target.value)} value={valorTitulo} />
        {sugerencia ? (
          <InlineSuggestion
            onIgnore={() => setSugerencia(false)}
            onUse={() => { setValorTitulo('Golden Axe'); setSugerencia(false); }}
            source="ArcadeDB"
            value="Golden Axe"
          />
        ) : <p>Sugerencia resuelta.</p>}
      </div>
    </section>
  );
}

using System.Collections;
using UnityEngine;
using Verse;

namespace TerminalKeeper
{
    /// <summary>
    /// Unity MonoBehaviour singleton that executes coroutines on the main thread.
    /// Needed because RimWorld mods do not have a natural MonoBehaviour to host coroutines.
    /// </summary>
    public class CoroutineHost : MonoBehaviour
    {
        private static CoroutineHost? _instance;

        private static CoroutineHost Instance
        {
            get
            {
                if (_instance != null) return _instance;
                var go = new GameObject("TerminalKeeper_CoroutineHost");
                DontDestroyOnLoad(go);
                _instance = go.AddComponent<CoroutineHost>();
                return _instance;
            }
        }

        public static Coroutine Start(IEnumerator routine) =>
            Instance.StartCoroutine(routine);
    }
}

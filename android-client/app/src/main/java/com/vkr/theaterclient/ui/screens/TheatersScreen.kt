package com.vkr.theaterclient.ui.screens

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.vkr.theaterclient.ui.TheaterViewModel

@Composable
fun TheatersScreen(
    viewModel: TheaterViewModel,
    onTheaterClick: (Int) -> Unit,
    onReservationsClick: () -> Unit,
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        viewModel.loadTheaters()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(text = "Театры", style = MaterialTheme.typography.headlineSmall)
        Button(onClick = onReservationsClick, modifier = Modifier.fillMaxWidth()) {
            Text("Мои брони")
        }
        if (state.loading) {
            Text("Загрузка...")
        }
        state.error?.let { Text(text = it, color = MaterialTheme.colorScheme.error) }
        if (!state.loading && state.theaters.isEmpty()) {
            Text("Список театров пуст.")
        }
        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(state.theaters, key = { it.theaterId }) { theater ->
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { onTheaterClick(theater.theaterId) },
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text(theater.name ?: "Без названия")
                        Text(theater.location ?: "", style = MaterialTheme.typography.bodySmall)
                    }
                }
            }
        }
    }
}

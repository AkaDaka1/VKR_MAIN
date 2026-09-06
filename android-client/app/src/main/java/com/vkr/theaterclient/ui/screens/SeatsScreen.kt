package com.vkr.theaterclient.ui.screens

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
fun SeatsScreen(
    showId: Int,
    viewModel: TheaterViewModel,
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    LaunchedEffect(showId) {
        viewModel.loadSeats(showId)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(text = "Выбор места", style = MaterialTheme.typography.headlineSmall)
        if (state.loading) Text("Загрузка...")
        state.error?.let { Text(text = it, color = MaterialTheme.colorScheme.error) }
        if (!state.loading && state.seats.isEmpty()) {
            Text("Нет доступных мест.")
        }

        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(state.seats, key = { it.ticketId }) { seat ->
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(modifier = Modifier.padding(12.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Text("Место: ${seat.seatNumber ?: "-"}")
                        Text("Статус: ${seat.status ?: "-"}")
                        Text("Цена: ${seat.price ?: 0.0}")
                        Button(
                            onClick = { seat.seatNumber?.let(viewModel::reserveSeat) },
                            enabled = seat.status == "available" && !state.loading,
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Text("Забронировать")
                        }
                    }
                }
            }
        }
    }
}

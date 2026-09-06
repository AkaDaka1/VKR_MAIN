package com.vkr.theaterclient.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
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
fun ReservationsScreen(viewModel: TheaterViewModel) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        viewModel.loadReservations()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Text(text = "Мои бронирования", style = MaterialTheme.typography.headlineSmall)
        if (state.loading) Text("Загрузка...")
        state.error?.let { Text(text = it, color = MaterialTheme.colorScheme.error) }
        if (!state.loading && state.reservations.isEmpty()) {
            Text("У вас пока нет бронирований.")
        }

        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(state.reservations, key = { it.ticketId }) { reservation ->
                Card {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text("Место: ${reservation.seatNumber ?: "-"}")
                        Text("Статус: ${reservation.status ?: "-"}")
                        Text("Цена: ${reservation.price ?: 0.0}")
                    }
                }
            }
        }
    }
}
